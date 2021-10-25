# Copyright 2021 the .NET Foundation
# Licensed under the MIT License

"""
The WWT kernel data relay Jupyter notebook server extension.
"""

import json
from queue import Empty

from tornado import gen, web

from jupyter_client.session import Session
from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler
from traitlets.config.configurable import LoggingConfigurable

__all__ = ["load_jupyter_server_extension"]


class SequencedBuffer(object):
    def __init__(self):
        self.next_seq = 0
        self.by_seq = {}

    def try_get_next(self):
        try:
            item = self.by_seq.pop(self.next_seq)
        except KeyError:
            return None

        self.next_seq += 1
        return item

    def accumulate(self, reply, log_object):
        seq = reply["content"].get("seq")
        if seq is None:
            log_object.log_warning("dropping message %r", reply)
            return

        # ignore old, duplicated messages
        if seq >= self.next_seq:
            self.by_seq[seq] = reply


class Registry(LoggingConfigurable):
    """
    A registry of kernels that have expressed an interest in publishing data files.
    """

    def __init__(self):
        self._kid_to_client = {}
        self._key_to_kid = {}
        self._mid_to_buffer = {}

    def log_debug(self, fmt, *args):
        self.log.debug("wwt_kernel_data_relay | " + fmt, *args)

    def log_info(self, fmt, *args):
        self.log.info("wwt_kernel_data_relay | " + fmt, *args)

    def log_warning(self, fmt, *args):
        self.log.warning("wwt_kernel_data_relay | " + fmt, *args)

    def watch_new_kernel(self, kernel_id, km):
        session = Session(
            config=km.session.config,
            key=km.session.key,
        )

        kc = km.client(session=session)
        self._kid_to_client[kernel_id] = kc

        stream = km.connect_iopub()
        self.log_debug("watching kernel %s in session %s", kernel_id, session.session)

        def watch_iopubs(msg_list):
            idents, fed_msg_list = session.feed_identities(msg_list)
            msg = session.deserialize(fed_msg_list)
            msg_type = msg["header"]["msg_type"]

            if msg_type == "wwtkdr_claim_key":
                key = msg["content"].get("key")

                if not key:
                    self.log_warning(
                        "missing/empty key specified in claim by kernel %s", kernel_id
                    )
                elif key.startswith("_"):
                    self.log_warning(
                        "kernel %s attempted to claim reserved key %s", kernel_id, key
                    )
                else:
                    self.log_debug("key %s claimed by kernel %s", key, kernel_id)
                    self._key_to_kid[key] = kernel_id

        stream.on_recv(watch_iopubs)

    def get_kernel_id(self, key):
        return self._key_to_kid.get(key)

    def get_client(self, mkm, kernel_id):
        # Hack (I think?) to check if the kernel is still alive
        try:
            km = mkm.get_kernel(kernel_id)
        except Exception as e:
            try:
                del self._kid_to_client[kernel_id]
            except KeyError:
                pass
            return None

        return self._kid_to_client.get(kernel_id)

    async def get_next_reply(self, msg_id, kc):
        """
        Get the next reply to one of our messages.

        This has to be centralized in the registry because we might retrieve
        replies to *other* requests, which need to be buffered so that those
        handlers get the data they need.

        This will raise queue.Empty if there really seems to be no next reply.
        """

        tries = 0

        while True:
            # Has a buffered message shown up? Note that even if our call to
            # get_shell_msg() raises an Empty error, someone *else* might have
            # gotten a message and buffered it while we were waiting.
            buffer = self._mid_to_buffer.get(msg_id)
            if buffer:
                reply = buffer.try_get_next()
                if reply is not None:
                    return reply

            # Nothing in our private buffer. Ask the kernel client.
            #
            # Depending on where we're being run, our kernel client may or may
            # not be async. I'm not aware of a way to ensure that the client is
            # async, so we just hackily try to handle both forms. Either the
            # get_shell_msg or the await might raise the queue.Empty error.
            try:
                reply = kc.get_shell_msg(timeout=1)
                if not isinstance(reply, dict):
                    reply = await reply
            except Empty:
                # It's possible that someone buffered up a reply for us while we
                # were waiting. But if we start waiting too long, give up.
                tries += 1

                if tries < 30:
                    continue
                else:
                    raise

            # OK, we got a reply. It might even be for us. But even if it is,
            # someone else might have buffered a *different*, earlier reply
            # intended for us. So the only tractable way to ensure that
            # everything stays ordered is to always use the buffer.

            reply_mid = reply["parent_header"].get("msg_id")

            if reply_mid is None:
                self.log_warning(
                    "dropping message on floor because it has no parent_id: %s", reply
                )
            else:
                buffer = self._mid_to_buffer.get(reply_mid)
                if buffer is None:
                    self._mid_to_buffer[reply_mid] = buffer = SequencedBuffer()
                buffer.accumulate(reply, self)

        # we never break out of the loop.

    def finish_reply_buffering(self, msg_id):
        """
        A helper to try to avoid unbounded growth of our reply buffer.
        """
        try:
            del self._mid_to_buffer[msg_id]
        except KeyError:
            pass


class DataRequestHandler(IPythonHandler):
    def initialize(self, registry):
        self.registry = registry

    async def get(self, key, entry):
        """
        Note that Tornado will already apply some URL normalization before we
        get to this point. In particular, some constructs like `/foo/../bar`
        will be converted to `/bar`. `foo//bar` will *not* be normalized,
        though, nor will trailing `/.` terms.
        """

        authenticated = bool(self.current_user)

        # This also includes the normalizations mentioned above.
        url = self.request.full_url()

        kernel_id = self.registry.get_kernel_id(key)
        if kernel_id is None:
            self.clear()
            self.set_status(404)
            self.finish(f"unrecognized WWTKDR key {key!r}")
            return

        self.registry.log_debug(
            "GET key=%s kernel_id=%s entry=%s authenticated=%s",
            key,
            kernel_id,
            entry,
            authenticated,
        )

        kc = self.registry.get_client(self.kernel_manager, kernel_id)
        if kc is None:
            self.clear()
            self.set_status(404)
            self.registry.log_warning(
                f"could not get kernel client for WWTKDR key {key!r}"
            )
            self.finish(f"could not get kernel client for WWTKDR key {key!r}")
            return

        content = dict(
            method="GET",
            url=url,
            authenticated=authenticated,
            key=key,
            entry=entry,
            # Special marker for "expedited" processing in pywwt Jupyter
            # clients, needed to make it possible for those clients to process
            # such requests while evaluating async Python code. Without this,
            # the user can't use an async command to ask the frontend to load a
            # WTML file describing tiled data, because the kernel won't be able
            # to process the KDR data request.
            data={"content": {"_pywwtExpedite": True}},
        )
        msg = kc.session.msg("wwtkdr_resource_request", content)
        msg_id = msg["header"]["msg_id"]
        kc.shell_channel.send(msg)

        self.clear()
        first = True
        keep_going = True

        while keep_going:
            # Get the next reply, using a centralized buffer to make sure that
            # we don't drop anything on the floor when simultaneous requests are
            # happening.
            try:
                reply = await self.registry.get_next_reply(msg_id, kc)
            except Empty:
                self.registry.finish_reply_buffering(msg_id)
                self.clear()
                self.set_status(500)
                self.registry.log_warning(
                    "incomplete or missing response from kernel | key=%s entry=%s kernel_id=%s msg_id=%s",
                    key,
                    entry,
                    kernel_id,
                    msg_id,
                )
                self.finish("incomplete or missing response from kernel")
                return

            content = reply["content"]
            status = content.get("status", "unspecified")

            if status != "ok":
                self.registry.finish_reply_buffering(msg_id)
                self.clear()
                self.set_status(500)
                msg = content.get("evalue", "unspecified kernel error")
                self.registry.log_warning(
                    "kernel internal error | %s | key=%s entry=%s kernel_id=%s",
                    msg,
                    key,
                    entry,
                    kernel_id,
                )
                self.finish(msg)
                return

            if first:
                self.set_status(content["http_status"])
                for name, value in content["http_headers"]:
                    self.set_header(name, value)
                first = False

            keep_going = content["more"] and len(reply["buffers"])

            for buf in reply["buffers"]:
                self.write(bytes(buf))

        self.registry.finish_reply_buffering(msg_id)
        self.finish()


class ProbeRequestHandler(IPythonHandler):
    @web.authenticated
    def get(self):
        info = {"status": "ok"}

        self.set_status(200)
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(info))
        self.finish()


def load_jupyter_server_extension(nb_server_app):
    """
    Initialize the server extension.

    The argument ``nb_server_app`` is an instance of
    ``notebook.notebookapp.NotebookWebApplication``.
    """

    web_app = nb_server_app.web_app
    host_pattern = ".*$"
    probe_route_pattern = url_path_join(web_app.settings["base_url"], "/wwtkdr/_probe")
    data_route_pattern = url_path_join(
        web_app.settings["base_url"], "/wwtkdr/([^/]*)/(.*)"
    )

    # The registry of kernels and URL "keys". Also slightly overloaded to
    # contain our logger.

    registry = Registry()

    # Register handlers.

    web_app.add_handlers(
        host_pattern,
        [
            (probe_route_pattern, ProbeRequestHandler),
            (data_route_pattern, DataRequestHandler, {"registry": registry}),
        ],
    )

    # In order for the registry to be notified of when a kernel has requested a
    # URL prefix, we need to shim ourselves into the kernel startup framework
    # and register a message listener.

    registry.log_info("shimming into notebook startup")
    app_km = nb_server_app.kernel_manager
    orig_start_watching_activity = app_km.start_watching_activity

    def shimmed_start_watching_activity(kernel_id):
        orig_start_watching_activity(kernel_id)
        km = app_km.get_kernel(kernel_id)
        registry.watch_new_kernel(kernel_id, km)

    app_km.start_watching_activity = shimmed_start_watching_activity
