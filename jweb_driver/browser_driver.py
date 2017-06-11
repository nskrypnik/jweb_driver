import asyncio
import sys
from .handler_wrappers import LoadHandlerWrapper, RequestHandlerWrapper
from .utils import are_urls_equal
from .js_functions import js_get_attr, js_is_element, js_click, js_fill_input, \
    js_get_text, js_get_html, js_get_location
from .exceptions import OperationTimeout, ElementNotFound, JavaScriptError
from PyQt4.QtWebKit import *
from PyQt4.QtCore import QUrl

BROWSER_LOOP_DELAY = 0.1

# result values
SUCCESS = 'success'
FAILED = 'failed'

# timeout constants
WAIT_TIMEOUT = 60
INTERVAL_TIMEOUT = 0.25

def singletask(func):
    '''Decorator for returning a future object which should be resolved by
    when method is completed and is canceled every time when new method is
    called
    '''
    async def wrapper(*args, **kw):
        driver = args[0]
        await driver.lock.acquire()
        driver.reset_async_primitives()
        result = await func(*args, **kw)
        driver.lock.release()
        return result
    return wrapper


class BrowserDriver:
    def __init__(self, loop):
        self.WAIT_TIMEOUT = 60
        self.INTERVAL_TIMEOUT = 0.25

        self.loop = loop
        self.lock = asyncio.Lock()
        self._init_browser()
        self.is_browser_running = False
        self.reset_async_primitives()

    def _init_browser(self):
        # if not self._cef_initialized:
        #     sys.excepthook = self.cef.ExceptHook  # To shutdown all CEF processes on error
        #     self.cef.Initialize({
        #         'log_severity': self.cef.LOGSEVERITY_DISABLE,
        #         'windowless_rendering_enabled': True,
        #         'debug': False
        #     })
        # self.browser = self.cef.CreateBrowserSync(browserSettings=dict(image_load_disabled=True))
        # self.browser.SetClientHandler(LoadHandlerWrapper(self))
        # self.browser.SetClientHandler(RequestHandlerWrapper(self))
        # # create JS bindings
        # self.js_bindings = self.cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
        # self.js_bindings.SetFunction('py_data_callback', self._py_data_callback)
        # self.js_bindings.SetFunction('py_handle_exception', self._py_handle_exception)
        # self.browser.SetJavascriptBindings(self.js_bindings)

        self.browser = QWebView()
        self.browser.page().loadFinished.connect(self.on_load_end)

    def javascript_callback(self, result):
        if result['success']:
            self._future.set_result(result.get('data', None))
        else:
            self._future.set_exception(JavaScriptError(result['error']))

    def run(self):
        self.browser.show()
        self.is_browser_running = True

    def shutdown(self):
        self.is_browser_running = False

    def reset_async_primitives(self):
        '''Reset async primitives Futur and Queue for current task context
        '''
        self._future = asyncio.Future()
        self._queue = asyncio.Queue()

    async def browser_message_loop(self):
        '''Run browser message loop within asyncio loop
        '''
        while True:
            self.cef.MessageLoopWork()
            await asyncio.sleep(BROWSER_LOOP_DELAY)

    # --------------------------------------------------
    # browser event handlers
    # --------------------------------------------------

    def on_load_end(self, ok):
        url = self.browser.page().currentFrame().url().toString()
        self._queue.put_nowait(dict(type='url', data=url))

    def on_resource_redirect(self, browser, frame, old_url, new_url_out, request, response):
        self._queue.put_nowait(dict(
            type='redirect',
            data=dict(
                old_url=old_url,
                new_url=new_url_out[0]
            )
        ))

    # --------------------------------------------------
    # browser commands below
    # --------------------------------------------------

    @singletask
    async def open_url(self, url='', timeout=WAIT_TIMEOUT):
        '''Open url in main frame
        '''
        self.browser.load(QUrl(url))
        res = await asyncio.wait_for(self._queue.get(), timeout)
        return res['data']

    @singletask
    async def get_attr(self, selector='', attr='', forall=False, safe=False):
        '''Get attribute of specified by selector element.
           If safe parameter is provided it won't raise an error in case when
           element is not found.
           Return a value of attribute or a list of values if forall is True
        '''
        js_get_attr(self, selector=selector, attr=attr, forall=forall)
        result = await self._future
        if not result and not safe:
            raise ElementNotFound(selector)
        return result

    @singletask
    async def wait_for(self, selector=None, url=None, timeout=WAIT_TIMEOUT, safe=False):
        '''Wait for url to be loaded or element reachable by selector.
           Return 1 for url if success and count of elements found with provided
           selector.
        '''
        max_attempts = int(timeout / INTERVAL_TIMEOUT)
        attempts = 0
        while True:
            attempts += 1
            if selector:
                js_is_element(self, selector=selector)
            if url:
                js_get_location(self)
            res = await self._future
            if selector:
                if res:
                    return res
            if url:
                if are_urls_equal(res, url):
                    return res
            if attempts > max_attempts:
                if not safe:
                    raise OperationTimeout(
                        'Timeout exceeded while waiting for %s' %
                        ('selector' if selector else 'url')
                    )
                return 0
            # reset it after each attempt
            self.reset_async_primitives()
            await asyncio.sleep(self.INTERVAL_TIMEOUT)


    @singletask
    async def is_element(self, selector=''):
        '''Check whether element exists in current document.
        '''
        js_is_element(self, selector=selector)
        return bool(await self._future)

    @singletask
    async def click(self, selector=''):
        '''Trigget click event on specific element reachable by selector
        '''
        js_is_element(self, selector=selector)
        result = await self._future
        if (result):
            self.reset_async_primitives()
            js_click(self, selector=selector)
            await self._future
            return True
        return False

    @singletask
    async def fill_input(self, selector='', value='', forall=False):
        '''Fill the input specified by selector
        '''
        js_is_element(self, selector=selector)
        result = await self._future
        if (result):
            self.reset_async_primitives()
            js_fill_input(self, selector=selector, value=value, forall=forall)
            await self._future
            return True
        return False

    @singletask
    async def get_text(self, selector='', forall=False, safe=False):
        '''Get text content of element specified by selector
        '''
        js_get_text(self, selector=selector, forall=forall)
        result = await self._future
        if result is None or result == []:
            if not safe:
                raise ElementNotFound(selector)
        return '' if result is None else result

    @singletask
    async def get_html(self, selector='', forall=False, safe=False):
        '''Get inner HTML of element specified by selector
        '''
        js_get_html(self, selector=selector, forall=forall)
        result = await self._future
        if result is None or result == []:
            if not safe:
                raise ElementNotFound(selector)
        return '' if result is None else result


    @singletask
    async def expect_redirect(self, url='', timeout=WAIT_TIMEOUT, safe=False):
        self.browser.load(QUrl(url))
        res = await asyncio.wait_for(self._queue.get(), timeout)
        return res['data']
