import asyncio
import base64
import inspect
import json
import logging
import os
import re
import shutil
import threading
import time
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

import tornado.gen
import tornado.ioloop
import tornado.web
from astropy.io import fits

from pytel import PytelModule
from pytel.object import get_object
from pytel.comm import RemoteException
from pytel.utils.fits import create_preview

log = logging.getLogger(__name__)


def auth_required(handler_class):
    def wrap_execute(handler_execute):
        def handle_auth(handler, kwargs):
            # get auth handlers
            auth_handlers = handler.application.auth_handlers
            if not auth_handlers:
                # if none are found, allow access
                return True

            # loop auth handlers
            success = False
            for auth_handler in auth_handlers:
                if auth_handler.check_login(request_handler=handler):
                    # successful login
                    success = True
                    break

            # no success?
            if not success:
                # get login handler
                login_handler = handler.application.login_handler
                if login_handler is not None:
                    login_handler(handler)
                else:
                    # just throw an 401
                    handler.set_status(401)
                    handler._transforms = []
                    handler.write('Access denied')
                    handler.finish()
                    return False

            # finished
            return success

        def _execute(self, transforms, *args, **kwargs):
            if not handle_auth(self, kwargs):
                return False
            return handler_execute(self, transforms, *args, **kwargs)

        return _execute

    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class


class JsonRpcException(Exception):
    def __init__(self, error_code, message):
        self.error_code = error_code
        self.message = message

    @property
    def error(self):
        return {
            'jsonrpc': '2.0',
            'error': {'code': self.error_code, 'message': self.message},
            'id': None
        }


class JsonRpcParseErrorException(JsonRpcException):
    def __init__(self):
        JsonRpcException.__init__(self, -32700, 'Parse error')


class JsonRpcInvalidRequestException(JsonRpcException):
    def __init__(self):
        JsonRpcException.__init__(self, -32600, 'Invalid request')


class JsonRpcMethodNotFoundException(JsonRpcException):
    def __init__(self, name=None):
        if name:
            JsonRpcException.__init__(self, -32601, 'Method "%s" not found' % name)
        else:
            JsonRpcException.__init__(self, -32601, 'Method not found')


class JsonRpcInvalidParamsException(JsonRpcException):
    def __init__(self):
        JsonRpcException.__init__(self, -32602, 'Invalid params')


class JsonRpcInternalErrorException(JsonRpcException):
    def __init__(self, e: Exception):
        # get class for exception
        class_name = e.__class__.__module__ + "." + e.__class__.__name__
        # get message
        tmp = str(e)
        error_msg = class_name + ((': ' + tmp) if len(tmp) < 0 else '')
        # init
        JsonRpcException.__init__(self, -32603, error_msg)


@auth_required
class JsonRpcHandler(tornado.web.RequestHandler):
    def initialize(self, executor):
        self.executor = executor

    @tornado.gen.coroutine
    def post(self):
        try:
            # get body and decode JSON
            try:
                jsonrpc = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                raise JsonRpcParseErrorException

            # we require some fields
            if 'jsonrpc' not in jsonrpc or jsonrpc['jsonrpc'] != '2.0' \
                    or 'method' not in jsonrpc or 'id' not in jsonrpc:
                raise JsonRpcInvalidRequestException

            # server methods start with an underscore
            server_methods = {
                '_get_modules': self.application.get_modules,
                '_ping': self.application.ping
            }

            # get parameters
            params = jsonrpc['params'] if 'params' in jsonrpc and jsonrpc['params'] is not None else {}

            # log
            if not any([regexp.match(jsonrpc['method']) for regexp in self.application.regexp_ignore_log]):
                log.info('(id#%d) Invoking %s(%s)...',
                         jsonrpc['id'], jsonrpc['method'], str(params)[1:-1] if params else '')

            # is it a server method?
            if jsonrpc['method'] in server_methods:
                # get method and signature
                method = server_methods[jsonrpc['method']]
                signature = inspect.signature(method)

                # bind parameters
                ba = signature.bind(**params)
                ba.apply_defaults()

                # call it
                response = yield self.executor.submit(method, **params)

            else:
                # split into method and module
                mod, method = jsonrpc['method'].split('.')

                # try to run method
                response = yield self.executor.submit(self.application.call_method, mod, method, **params)

            # build response body
            log.info('(id#%d) Sending response: %s', jsonrpc['id'], str(response))
            response_body = {'jsonrpc': '2.0', 'result': response, 'id': jsonrpc['id']}

            # send response
            self.set_header('Content-Disposition', 'attachment; filename="image.json')
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps(response_body))

        except JsonRpcException as e:
            # write error message
            self.write(json.dumps(e.error))

        finally:
            try:
                # finish stream
                yield self.flush()
            finally:
                pass


@auth_required
class DownloadFileHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, filename):
        # get data
        try:
            log.info('Sending file %s...', filename)

            # load file
            with self.application.open_file(filename, 'rb', compression=False) as f:
                # get filename without scheme and path
                filename = os.path.basename(filename)

                # set response headers
                self.set_header('Content-type', 'image/fits')
                self.set_header('Content-Disposition', 'attachment; filename="{0}'.format(filename))

                # send data
                while True:
                    # read chunk
                    data = f.read(1024*1024)

                    # no data? finished!
                    if len(data) == 0:
                        break

                    # write data and flush stream
                    self.write(data)
                    yield self.flush()

                # finished with file
                self.finish()

        except FileNotFoundError:
            log.error('Could not download image.')
            raise tornado.web.HTTPError(404)


class Cache(object):
    Entry = namedtuple('Entry', 'time filename data')

    def __init__(self, size=10):
        self._entries = []
        self._size = size

    def __setitem__(self, filename, data):
        # append
        self._entries.append(Cache.Entry(time.time(), filename, data))

        # too many entries?
        if len(self._entries) > self._size:
            # sort by time diff
            now = time.time()
            self._entries.sort(key=lambda e: now - e.time)

            # pick first
            self._entries = self._entries[:self._size]

    def __getitem__(self, filename):
        for e in self._entries:
            if e.filename == filename:
                return e.data
        raise IndexError

    def __contains__(self, filename):
        for e in self._entries:
            if e.filename == filename:
                return True
        return False


@auth_required
class PreviewHandler(tornado.web.RequestHandler):
    _preview_cache = Cache()

    @tornado.gen.coroutine
    def get(self, filename):
        # not in headers cache already?
        if filename not in self._preview_cache:
            try:
                # download fits file
                with self.application.open_file(filename, 'rb') as f:
                    # get data
                    hdus = fits.open(f, memmap=False)
                    data = create_preview(hdus[0], buffer=True)
                    hdus.close()

                    # store it
                    self._preview_cache[filename] = data

            except FileNotFoundError:
                log.error('Could not download image.')
                raise tornado.web.HTTPError(404)

        # get data
        data = self._preview_cache[filename]

        # send it
        log.info('Sending preview for %s...', filename)
        self.set_header('Content-type', 'image/png')
        self.set_header('Content-Disposition', 'inline; filename="image.png')
        self.write(data)
        yield self.flush()


@auth_required
class HeadersHandler(tornado.web.RequestHandler):
    _headers_cache = Cache()

    @tornado.gen.coroutine
    def get(self, filename):
        # not in headers cache already?
        if filename not in self._headers_cache:
            try:
                # download fits file
                with self.application.open_file(filename, 'rb') as f:
                    # get data
                    hdus = fits.open(f, memmap=False)
                    data = {key: [value, ''] for key, value in hdus[0].header.items()}
                    hdus.close()

                    # store it
                    self._headers_cache[filename] = data

            except FileNotFoundError:
                log.error('Could not download image.')
                raise tornado.web.HTTPError(404)

        # get data
        data = self._headers_cache[filename]

        # send it
        log.info('Sending FITS headers for %s...', filename)
        self.set_header('Content-type', 'application/json')
        self.set_header('Content-Disposition', 'inline; filename="%s"' % filename[filename.rfind('/') + 1:])
        self.write(bytes(json.dumps(data), 'utf-8'))
        yield self.flush()


@auth_required
class AngularHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, path):
        # default
        if path == '' or path not in self.application.files:
            path = self.application.base_href + 'index.html'

        # mime type
        if path.endswith('.html'):
            self.set_header('Content-Type', 'text/html')
        elif path.endswith('.js'):
            self.set_header('Content-Type', 'application/javascript')
        elif path.endswith('.css'):
            self.set_header('Content-Type', 'text/css')
        elif path.endswith('.txt'):
            self.set_header('Content-Type', 'text/plain')

        # send data
        self.write(self.application.files[path])
        yield self.flush()


class HTTP2XMPP(PytelModule, tornado.web.Application):
    def __init__(self, port: int = 37077, auth: dict = None, ignore_log: list = None, base_href: str = '/pytel/',
                 web_config: dict = None, public_html: str = None, *args, **kwargs):
        self.executor = ThreadPoolExecutor(max_workers=30)
        PytelModule.__init__(self, thread_funcs=self._http, *args, **kwargs)

        # store
        self._port = port
        self._base_href = base_href

        # auth/login handlers
        self._auth_handlers = []
        if auth is not None and 'handler' in auth and auth['handler'] is not None:
            # make a list, if necessary
            configs = auth['handler'] if isinstance(auth['handler'], list) else [auth['handler']]
            # create databases
            self._auth_handlers = [get_object(c) for c in configs]
        self._login_handler = None
        if auth is not None and 'login' in auth and auth['login'] is not None:
            self._login_handler = get_object(auth['login'])

        # load static files
        log.info('Loading static files...')
        self.files = {}
        self._load_static_files(public_html)

        # overwrite config
        self._load_web_config(web_config, base_href)

        # define routes
        href = base_href
        routes = [
            (href + r'jsonrpc', JsonRpcHandler, {'executor': self.executor}),
            (href + r'download/(.*)', DownloadFileHandler),
            (href + r'preview/(.*)', PreviewHandler),
            (href + r'headers/(.*)', HeadersHandler),
            (r'(.*)', AngularHandler)
        ]

        # add default route, if href is given
        if href is not None and len(href) > 0:
            routes.append(('.*', tornado.web.RedirectHandler, {'url': href}))

        # init tornado app
        tornado.web.Application.__init__(self, routes)

        # stuff
        self._io_loop = None
        self._auth = None
        self._proxies = {}
        self._lock = threading.RLock()
        self.regexp_ignore_log = [re.compile(i) for i in ignore_log] if ignore_log else []

    @property
    def auth_handlers(self):
        return self._auth_handlers

    @property
    def login_handler(self):
        return self._login_handler

    @property
    def base_href(self):
        return self._base_href

    def _load_static_files(self, path, rel_path=''):
        for x in os.listdir(path):
            # get full and relative path
            full = os.path.join(path, x)
            rel = os.path.join(rel_path, x)

            # is it a directory or file?
            if os.path.isdir(full):
                # go deeper
                self._load_static_files(full, rel_path=os.path.join(rel_path, x))
            elif os.path.isfile(full):
                # load it
                with open(full, 'rb') as f:
                    self.files[self._base_href + rel] = f.read()

    def _load_web_config(self, web_config: dict, base_href: str):
        if web_config:
            for name, config in web_config.items():
                filename = os.path.join(base_href, name)
                self.files[filename] = json.dumps(config)

    def _http(self):
        # create io loop
        asyncio.set_event_loop(asyncio.new_event_loop())
        self._io_loop = tornado.ioloop.IOLoop.current()
        self._io_loop.make_current()

        # start listening
        log.info('Starting HTTP proxy on port %d...', self._port)
        self.listen(self._port)

        # start the io loop
        self._io_loop.start()

    def close(self):
        #self._io_loop.stop()
        self._io_loop.add_callback(self._io_loop.stop)
        PytelModule.close(self)

    def call_method(self, user, method, *args, **kwargs):
        # call method
        try:
            # get proxy
            with self._lock:
                if user not in self._proxies:
                    self._proxies[user] = self.comm[user]
                proxy = self._proxies[user]

            # execute it
            return proxy.execute(method, *args, **kwargs)
        except RemoteException:
            # not possible
            raise JsonRpcMethodNotFoundException
        except Exception as e:
            # log error
            logging.exception('Something went wrong.')
            raise JsonRpcInternalErrorException(e)

    def get_modules(self):
        modules = []
        for mod in self.comm.clients:
            # get proxy
            proxy = self.comm[mod]
            if proxy is None:
                log.debug('Could not find module %s.', mod)
                continue

            # append only, if at least one interface is implemented
            if len(proxy.interfaces) > 0:
                modules.append({
                    'module': mod[:mod.find('@')],
                    'name': 'Test',
                    'interfaces': [i.__name__ for i in proxy.interfaces]
                })

        return modules

    def ping(self):
        return 'pong'
