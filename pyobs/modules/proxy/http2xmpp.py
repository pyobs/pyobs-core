import asyncio
import inspect
import json
import logging
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
import tornado.gen
import tornado.ioloop
import tornado.web
from astropy.io import fits

from pyobs import PyObsModule
from pyobs.object import get_object
from pyobs.comm import RemoteException
from pyobs.utils.cache import DataCache
from pyobs.utils.fits import create_preview
from pyobs.auth import tornado_auth_required

log = logging.getLogger(__name__)


class JsonRpcException(Exception):
    """Base class for JSON RPC exceptions."""

    def __init__(self, error_code: int, message: str):
        """Initializes new exception.

        Args:
            error_code: The JSON RPC error code.
            message: Error message.
        """
        self.error_code = error_code
        self.message = message

    @property
    def error(self):
        """Return the JSON for this exception."""
        return {
            'jsonrpc': '2.0',
            'error': {'code': self.error_code, 'message': self.message},
            'id': None
        }


class JsonRpcParseErrorException(JsonRpcException):
    """Exception that is thrown when JSON cannot be parsed."""
    def __init__(self):
        JsonRpcException.__init__(self, -32700, 'Parse error')


class JsonRpcInvalidRequestException(JsonRpcException):
    """Exception that is thrown when the request is invalid."""
    def __init__(self):
        JsonRpcException.__init__(self, -32600, 'Invalid request')


class JsonRpcMethodNotFoundException(JsonRpcException):
    """Exception that is thrown when the requested method does not exist."""
    def __init__(self, name=None):
        if name:
            JsonRpcException.__init__(self, -32601, 'Method "%s" not found' % name)
        else:
            JsonRpcException.__init__(self, -32601, 'Method not found')


class JsonRpcInvalidParamsException(JsonRpcException):
    """Exception that is thrown when the request contains invalid parameters for the method."""
    def __init__(self):
        JsonRpcException.__init__(self, -32602, 'Invalid params')


class JsonRpcInternalErrorException(JsonRpcException):
    """Exception that is thrown on all other errors, mostly includes the thrown exception."""
    def __init__(self, e: Exception):
        # get class for exception
        class_name = e.__class__.__module__ + "." + e.__class__.__name__
        # get message
        tmp = str(e)
        error_msg = class_name + ((': ' + tmp) if len(tmp) < 0 else '')
        # init
        JsonRpcException.__init__(self, -32603, error_msg)


@tornado_auth_required
class JsonRpcHandler(tornado.web.RequestHandler):
    """Tornado reqest handler for JSON RPC calls."""

    def initialize(self, executor):
        """Initializes the handler (instead of in the constructor).

        Args:
            executor: A thread pool executor to use.
        """
        self.executor = executor

    @tornado.gen.coroutine
    def post(self):
        """Handle JSON RPC call."""

        # better safe than sorry...
        try:
            # get body and decode JSON
            try:
                rpc = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                raise JsonRpcParseErrorException

            # we require some fields
            if 'jsonrpc' not in rpc or rpc['jsonrpc'] != '2.0' or 'method' not in rpc or 'id' not in rpc:
                raise JsonRpcInvalidRequestException

            # server methods start with an underscore
            server_methods = {
                '_get_modules': self.application.get_modules,
                '_ping': self.application.ping
            }

            # get parameters
            params = rpc['params'] if 'params' in rpc and rpc['params'] is not None else {}

            # log
            if not any([regexp.match(rpc['method']) for regexp in self.application.regexp_ignore_log]):
                log.info('(id#%d) Invoking %s(%s)...',
                         rpc['id'], rpc['method'], str(params)[1:-1] if params else '')

            # is it a server method?
            if rpc['method'] in server_methods:
                # get method and signature
                method = server_methods[rpc['method']]
                signature = inspect.signature(method)

                # bind parameters
                ba = signature.bind(**params)
                ba.apply_defaults()

                # call it
                response = yield self.executor.submit(method, **params)

            else:
                # split into method and module
                mod, method = rpc['method'].split('.')

                # try to run method
                response = yield self.executor.submit(self.application.call_method, mod, method, **params)

            # build response body
            log.info('(id#%d) Sending response: %s', rpc['id'], str(response))
            response_body = {'jsonrpc': '2.0', 'result': response, 'id': rpc['id']}

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
                # give up...
                pass


@tornado_auth_required
class DownloadFileHandler(tornado.web.RequestHandler):
    """Handle download of files."""

    @tornado.gen.coroutine
    def get(self, filename: str):
        """Send requested file.

        Args:
            filename: Name of file to send.
        """

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


@tornado_auth_required
class PreviewHandler(tornado.web.RequestHandler):
    """Handle preview images."""

    """File cache."""
    _preview_cache = DataCache()

    @tornado.gen.coroutine
    def get(self, filename: str):
        """Send preview image for requested file.

        Args:
            filename: Name of image to get preview for.
        """

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


@tornado_auth_required
class HeadersHandler(tornado.web.RequestHandler):
    """Handle header requests."""

    """Data cache."""
    _headers_cache = DataCache()

    @tornado.gen.coroutine
    def get(self, filename):
        """Send FITS headers for requested file.

        Args:
            filename: Name of image to get fits headers for.
        """

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


@tornado_auth_required
class AngularHandler(tornado.web.RequestHandler):
    """Handle web requests for an Angular web app."""

    @tornado.gen.coroutine
    def get(self, path: str):
        """Send file.

        Args:
            path: Path to requested file.
        """

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


class HTTP2XMPP(PyObsModule, tornado.web.Application):
    """HTTP to XMPP proxy server."""

    def __init__(self, port: int = 37077, auth: dict = None, ignore_log: list = None, base_href: str = '/pyobs/',
                 web_config: dict = None, public_html: str = None, *args, **kwargs):
        """Initialize new proxy server.

        Args:
            port: Port for HTTP server.
            auth: Authentication module for HTTP.
            ignore_log: List of regular expression for methods that should NOT be logged.
            base_href: base_href for web app.
            web_config: Configuration for Angular web app.
            public_html: Path to Angular web app.
        """
        PyObsModule.__init__(self, thread_funcs=self._http, *args, **kwargs)

        # create thread pool executor
        self.executor = ThreadPoolExecutor(max_workers=30)

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
        if public_html is not None:
            self._load_static_files(public_html)

        # overwrite config
        self._load_web_config(web_config, base_href)

        # define routes
        href = base_href
        routes = [
            (href + r'jsonrpc', JsonRpcHandler, {'executor': self.executor}),
            (href + r'download/(.*)', DownloadFileHandler),
            (href + r'preview/(.*)', PreviewHandler),
            (href + r'headers/(.*)', HeadersHandler)
        ]

        # angular?
        if public_html is not None:
            routes.append((r'(.*)', AngularHandler))

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
        """Return authentification handlers."""
        return self._auth_handlers

    @property
    def login_handler(self):
        """Return login handlers."""
        return self._login_handler

    @property
    def base_href(self):
        """Return base href."""
        return self._base_href

    def _load_static_files(self, path: str, rel_path: str = ''):
        """Load static files from path.

        Args:
            path: Path to look for static files.
            rel_path: Relative path on web server.
        """

        # walk directory
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
        """Load web app configuration.

        Args:
            web_config: Dictionary of filename->config configuration files.
            base_href: Base href.
        """

        # actually got a web config?
        if web_config:
            # loop them
            for name, config in web_config.items():
                # get web file name
                filename = os.path.join(base_href, name)
                # store config
                self.files[filename] = json.dumps(config)

    def _http(self):
        """Thread function for the web server."""

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
        """Close server."""

        # close io loop and parent
        self._io_loop.add_callback(self._io_loop.stop)
        PyObsModule.close(self)

    def call_method(self, client: str, method: str, *args, **kwargs):
        """Call a method.

        Args:
            client: Client to call method on.
            method: Method to call.
            *args, **kwargs: Parameters for method.

        Returns:
            Method result.

        Raises:
            JsonRpcMethodNotFoundException: If method was not found.
            JsonRpcInternalErrorException: If something else went wrong.
        """

        # call method
        try:
            # get proxy
            with self._lock:
                if client not in self._proxies:
                    self._proxies[client] = self.comm[client]
                proxy = self._proxies[client]

            # execute it
            return proxy.execute(method, *args, **kwargs)
        except RemoteException:
            # not possible
            logging.exception('Something went wrong.')
            raise JsonRpcMethodNotFoundException(client + '.' + method)
        except Exception as e:
            # log error
            logging.exception('Something went wrong.')
            raise JsonRpcInternalErrorException(e)

    def get_modules(self) -> list:
        """Get a list of all available modules/clients.

        Returns:
            List of modules.
        """

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
                    'module': mod,
                    'name': 'Test',
                    'interfaces': [i.__name__ for i in proxy.interfaces]
                })

        return modules

    def ping(self):
        """Ping function."""
        return 'pong'


__all__ = ['HTTP2XMPP']
