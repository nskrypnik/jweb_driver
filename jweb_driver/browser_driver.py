import asyncio
import sys
from cefpython3 import cefpython as cef
from .handler_wrappers import LoadHandlerWrapper, RequestHandlerWrapper
from .utils import are_urls_equal
from .js_functions import js_get_attr, js_is_element, js_click, js_fill_input, \
    js_get_text, js_get_html
from .exceptions import OperationTimeout, ElementNotFound, JavaScriptError

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
        sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
        cef.Initialize({
            'log_severity': cef.LOGSEVERITY_DISABLE,
            'windowless_rendering_enabled': True,
            'debug': False
        })
        self.browser = cef.CreateBrowserSync(browserSettings=dict(image_load_disabled=True))
        self.browser.SetClientHandler(LoadHandlerWrapper(self))
        self.browser.SetClientHandler(RequestHandlerWrapper(self))
        # create JS bindings
        self.js_bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
        self.js_bindings.SetFunction('py_data_callback', self._py_data_callback)
        self.js_bindings.SetFunction('py_handle_exception', self._py_handle_exception)
        self.browser.SetJavascriptBindings(self.js_bindings)

    def _py_data_callback(self, js_data):
        '''Handle data set from JavaScript code
        '''
        self._future.set_result(js_data)

    def _py_handle_exception(self, js_error):
        '''Handle JavaScript exception caught while executing code
        '''
        self._future.set_exception(JavaScriptError(js_error))

    def run(self):
        self.loop.create_task(self.browser_message_loop())
        self.is_browser_running = True

    def shutdown(self):
        cef.shutdown()

    def reset_async_primitives(self):
        '''Reset async primitives Futur and Queue for current task context
        '''
        self._future = asyncio.Future()
        self._queue = asyncio.Queue()

    async def browser_message_loop(self):
        '''Run browser message loop within asyncio loop
        '''
        while True:
            cef.MessageLoopWork()
            await asyncio.sleep(BROWSER_LOOP_DELAY)

    # --------------------------------------------------
    # browser event handlers
    # --------------------------------------------------

    def on_load_end(self, browser, frame, http_code):
        self._queue.put_nowait(dict(type='url', data=frame.GetUrl()))

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
    async def open_url(self, url=''):
        '''Open url in main frame
        '''
        frame = self.browser.GetMainFrame()
        frame.LoadUrl(url)
        while True:
            msg = await self._queue.get()
            if msg['type'] == 'redirect' and are_urls_equal(msg['data']['old_url'], url):
                # redirect occured for original url
                url = msg['data']['new_url'] # update url
            if msg['type'] == 'url' and are_urls_equal(msg['data'], url):
                return url

    @singletask
    async def get_attr(self, selector='', attr='', forall=False, safe=False):
        '''Get attribute of specified by selector element.
           If safe parameter is provided it won't raise an error in case when
           element is not found.
           Return a value of attribute or a list of values if forall is True
        '''
        js_get_attr(self.browser, selector=selector, attr=attr, forall=forall)
        result = await self._future
        if not result and not safe:
            raise ElementNotFound(selector)
        return result

    @singletask
    async def wait_for(self, selector=None, url=None, timeout=WAIT_TIMEOUT):
        '''Wait for url to be loaded or element reachable by selector.
           Return 1 for url if success and count of elements found with provided
           selector.
        '''
        if url:
            while True:
                msg = asyncio.wait_for(self._queue.get(), timeout)
                if msg['type'] == 'url' and are_urls_equal(msg['data'], url):
                    return 1
        if selector:
            max_attempts = int(timeout / INTERVAL_TIMEOUT)
            attempts = 0
            while True:
                attempts += 1
                js_is_element(self.browser, selector=selector)
                count = await self._future
                if count:
                    return count
                if attempts > max_attempts:
                    raise OperationTimeout('Timeout exceeded while waiting for selector')
                # reset it after each attempt
                self.reset_async_primitives()
                await asyncio.sleep(self.INTERVAL_TIMEOUT)

    @singletask
    async def is_element(self, selector=''):
        '''Check whether element exists in current document.
        '''
        js_is_element(self.browser, selector=selector)
        return bool(await self._future)

    @singletask
    async def click(self, selector=''):
        '''Trigget click event on specific element reachable by selector
        '''
        js_is_element(self.browser, selector=selector)
        result = await self._future
        if (result):
            self.reset_async_primitives()
            js_click(self.browser, selector=selector)
            await self._future
            return True
        return False

    @singletask
    async def fill_input(self, selector='', value='', forall=False):
        '''Fill the input specified by selector
        '''
        js_is_element(self.browser, selector=selector)
        result = await self._future
        if (result):
            self.reset_async_primitives()
            js_fill_input(self.browser, selector=selector, value=value, forall=forall)
            await self._future
            return True
        return False

    @singletask
    async def get_text(self, selector='', forall=False, safe=False):
        '''Get text content of element specified by selector
        '''
        js_get_text(self.browser, selector=selector, forall=forall)
        result = await self._future
        if result is None or result == []:
            if not safe:
                raise ElementNotFound(selector)
        return '' if result is None else result

    @singletask
    async def get_html(self, selector='', forall=False, safe=False):
        '''Get inner HTML of element specified by selector
        '''
        js_get_html(self.browser, selector=selector, forall=forall)
        result = await self._future
        if result is None or result == []:
            if not safe:
                raise ElementNotFound(selector)
        return '' if result is None else result
