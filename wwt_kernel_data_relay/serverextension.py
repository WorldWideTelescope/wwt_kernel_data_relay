# Copyright 2021 the .NET Foundation
# Licensed under the MIT License

"""
The WWT kernel data relay Jupyter notebook server extension.
"""

from queue import Empty

from tornado import gen

from jupyter_client.session import Session
from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler
from traitlets.config.configurable import LoggingConfigurable

__all__ = ['load_jupyter_server_extension']


class Registry(LoggingConfigurable):
    """
    A registry of kernels that have expressed an interest in publishing data files.
    """

    def __init__(self):
        self._key_to_kid = {}

    def log_debug(self, fmt, *args):
        self.log.debug('wwt_kernel_data_relay | ' + fmt, *args)

    def log_info(self, fmt, *args):
        self.log.info('wwt_kernel_data_relay | ' + fmt, *args)

    def log_warning(self, fmt, *args):
        self.log.warning('wwt_kernel_data_relay | ' + fmt, *args)

    def watch_new_kernel(self, kernel_id, km):
        session = Session(
            config = km.session.config,
            key = km.session.key,
        )

        stream = km.connect_iopub()
        self.log_debug('watching kernel %s', kernel_id)

        def watch_iopubs(msg_list):
            idents, fed_msg_list = session.feed_identities(msg_list)
            msg = session.deserialize(fed_msg_list)
            msg_type = msg['header']['msg_type']

            if msg_type == 'wwtkdr_claim_key':
                key = msg['content'].get('key')

                if not key:
                    self.log_warning('missing/empty key specified in claim by kernel %s', kernel_id)
                else:
                    self.log_debug('key %s claimed by kernel %s', key, kernel_id)
                    self._key_to_kid[key] = kernel_id

        stream.on_recv(watch_iopubs)

    def get(self, key):
        return self._key_to_kid.get(key)


class DataRequestHandler(IPythonHandler):
    def initialize(self, registry):
        self.registry = registry

    @gen.coroutine
    def get(self, key, entry):
        """
        Note that Tornado will already apply some URL normalization before we
        get to this point. In particular, some constructs like `/foo/../bar`
        will be converted to `/bar`. `foo//bar` will *not* be normalized,
        though, nor will trailing `/.` terms.
        """

        authenticated = bool(self.current_user)

        kernel_id = self.registry.get(key)
        if kernel_id is None:
            self.clear()
            self.set_status(404)
            self.finish(f'unrecognized WWTKDR key {key!r}')
            return

        try:
            km = self.kernel_manager.get_kernel(kernel_id)
        except Exception as e:
            self.clear()
            self.set_status(404)
            self.finish(f'could not get kernel for WWTKDR key {key!r}: {e}')
            return

        self.registry.log_debug(
            'GET key=%s kernel_id=%s entry=%s authenticated=%s',
            key, kernel_id, entry, authenticated,
        )

        kc = km.client()

        content = dict(
            method = 'GET',
            authenticated = authenticated,
            key = key,
            entry = entry,
        )
        msg = kc.session.msg('wwtkdr_resource_request', content)
        msg_id = msg['header']['msg_id']
        kc.shell_channel.send(msg)

        self.clear()
        first = True
        keep_going = True

        while keep_going:
            try:
                reply = yield kc.get_shell_msg(timeout=10)
            except Empty:
                self.clear()
                self.set_status(500)
                msg = content.get('evalue', 'incomplete or missing reponse from kernel')
                self.finish(msg)
                return

            if reply['parent_header'].get('msg_id') != msg_id:
                continue  # not my message

            content = reply['content']
            status = content.get('status', 'unspecified')

            if status != 'ok':
                self.clear()
                self.set_status(500)
                msg = content.get('evalue', 'unspecified kernel error')
                self.finish(msg)
                return

            if first:
                self.set_status(content['http_status'])
                for name, value in content['http_headers']:
                    self.set_header(name, value)
                first = False

            keep_going = content['more'] and len(reply['buffers'])

            for buf in reply['buffers']:
                self.write(bytes(buf))

        self.finish()


def load_jupyter_server_extension(nb_server_app):
    """
    Initialize the server extension.

    The argument ``nb_server_app`` is an instance of
    ``notebook.notebookapp.NotebookWebApplication``.
    """

    web_app = nb_server_app.web_app
    host_pattern = '.*$'
    route_pattern = url_path_join(web_app.settings['base_url'], '/wwtkdr/([^/]*)/(.*)')

    # The registry of kernels and URL "keys". Also slightly overloaded to
    # contain our logger.

    registry = Registry()

    # Register our handler that will relay requests for data files.

    web_app.add_handlers(host_pattern, [
        (route_pattern, DataRequestHandler, {'registry': registry}),
    ])

    # In order for the registry to be notified of when a kernel has requested a
    # URL prefix, we need to shim ourselves into the kernel startup framework
    # and register a message listener.

    registry.log_info('shimming into notebook startup')
    app_km = nb_server_app.kernel_manager
    orig_start_watching_activity = app_km.start_watching_activity

    def shimmed_start_watching_activity(kernel_id):
        orig_start_watching_activity(kernel_id)
        km = app_km.get_kernel(kernel_id)
        registry.watch_new_kernel(kernel_id, km)

    app_km.start_watching_activity = shimmed_start_watching_activity
