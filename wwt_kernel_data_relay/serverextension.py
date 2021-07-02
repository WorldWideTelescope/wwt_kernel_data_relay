# Copyright 2021 the .NET Foundation
# Licensed under the MIT License

"""
The WWT kernel data relay Jupyter notebook server extension.
"""

from tornado import gen

from jupyter_client.session import Session
from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler

__all__ = ['load_jupyter_server_extension']


class Registry(object):
    """
    A registry of kernels that have expressed an interest in publishing data files.
    """

    def __init__(self):
        self._key_to_kid = {}

    def watch_new_kernel(self, kernel_id, km):
        session = Session(
            config = km.session.config,
            key = km.session.key,
        )

        stream = km.connect_iopub()
        print('WWTKDR: watching kernel', kernel_id)

        def watch_iopubs(msg_list):
            idents, fed_msg_list = session.feed_identities(msg_list)
            msg = session.deserialize(fed_msg_list)
            msg_type = msg['header']['msg_type']

            if msg_type == 'wwtkdr_claim_key':
                key = msg['content'].get('key')

                if not key:
                    print('WWTKDR: missing/empty key in claim?')
                else:
                    print(f'WWTKDR: key {key} claimed by kernel {kernel_id}')
                    self._key_to_kid[key] = kernel_id

        stream.on_recv(watch_iopubs)

    def get(self, key):
        return self._key_to_kid.get(key)


class DataRequestHandler(IPythonHandler):
    def initialize(self, registry):
        self.registry = registry

    @gen.coroutine
    def get(self, key, entry):
        authenticated = bool(self.current_user)

        print('************* WWTKDR HANDLER *****************')
        print('auth:', authenticated)
        print('key:', key)
        print('entry:', entry)

        kernel_id = self.registry.get(key)
        if kernel_id is None:
            self.clear()
            self.set_status(404)
            self.finish(f'unrecognized WWTKDR key {key!r}')
            return
        print('kernel_id:', kernel_id)

        try:
            km = self.kernel_manager.get_kernel(kernel_id)
        except Exception as e:
            self.clear()
            self.set_status(404)
            self.finish(f'could not get kernel for WWTKDR key {key!r}: {e}')
            return

        kc = km.client()

        content = dict(
            method = 'GET',
            entry = entry,
        )
        msg = kc.session.msg('wwtkdr_resource_request', content)
        msg_id = msg['header']['msg_id']
        kc.shell_channel.send(msg)
        self.clear()
        self.set_header('Content-Type', 'image/png') # XXXXXXXXXX

        while True:
            reply = yield kc.get_shell_msg(timeout=30)
            print('============= reply:')
            print(reply)
            print('====================')

            if reply['parent_header'].get('msg_id') != msg_id:
                print('** not my message')
                continue

            status = reply['content'].get('status', 'unspecified')
            if status != 'ok':
                raise HTTPError(500)

            if not len(reply['buffers']):
                break

            self.write(bytes(reply['buffers'][0]))

        self.finish(b'')


def load_jupyter_server_extension(nb_server_app):
    """
    Initialize the server extension.

    The argument ``nb_server_app`` is an instance of
    ``notebook.notebookapp.NotebookWebApplication``.
    """

    web_app = nb_server_app.web_app
    host_pattern = '.*$'
    route_pattern = url_path_join(web_app.settings['base_url'], '/wwtkdr/([^/]*)/(.*)')

    # The registry of kernels and URL "keys"

    registry = Registry()

    # Register our handler that will relay requests for data files.

    web_app.add_handlers(host_pattern, [
        (route_pattern, DataRequestHandler, {'registry': registry}),
    ])

    # In order for the registry to be notified of when a kernel has requested a
    # URL prefix, we need to shim ourselves into the kernel startup framework
    # and register a message listener.

    app_km = nb_server_app.kernel_manager
    orig_start_watching_activity = app_km.start_watching_activity

    def shimmed_start_watching_activity(kernel_id):
        orig_start_watching_activity(kernel_id)
        km = app_km.get_kernel(kernel_id)
        registry.watch_new_kernel(kernel_id, km)

    app_km.start_watching_activity = shimmed_start_watching_activity
