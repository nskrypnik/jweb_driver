import asyncio
import sys
from cefpython3 import cefpython as cef
from .handler_wrappers import LoadHandlerWrapper, RequestHandlerWrapper
from .utils import are_urls_equal
from .js_functions import js_get_attr, js_is_element

BROWSER_LOOP_DELAY = 0.1

# result values
SUCCESS = 'success'
FAILED = 'failed'

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
        self.MAX_POLLING = 200

        self.loop = loop
        self.lock = asyncio.Lock()
        self._init_browser()
        self.is_browser_running = False
        self.reset_async_primitives()

    def _init_browser(self):
        sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
        cef.Initialize()
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
        self._future.set_exception(dict(
            name=js_error.name,
            message=js_error.message,
            stack=js_error.stack
        ))

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
    async def open_url(self, url):
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
                return dict(method='openurl', result=SUCCESS, data=url)

    @singletask
    async def get_attr(self, selector, attr, forall=False):
        js_get_attr(self.browser, selector=selector, attr=attr, forall=forall)
        result = await self._future
        if not result:
            result = {}
        result.update(dict(method='get_attr'))
        if not 'data' in result:
            result.update(result=FAILED, msg='Element isn\'t found')
        else:
            result.update(dict(result=SUCCESS))
        return result

    @singletask
    async def wait_for(self, url=None, selector=None):
        result = dict(method='wait_for')
        if url:
            while True:
                try:
                    msg = asyncio.wait_for(self._queue.get(), self.WAIT_TIMEOUT)
                except asyncio.TimeoutError:
                    result.update(dict(
                        result=FAILED,
                        msg='Timout occured while waiting for url'
                    ))
                    return result
                if msg['type'] == 'url' and are_urls_equal(msg['data'], url):
                    result.update(dict(result=SUCCESS))
                    return result
        if selector:
            attempts = 0
            while True:
                attempts += 1
                js_is_element(self.browser, selector=selector)
                count = await self._future
                if count:
                    result.update(dict(result=SUCCESS))
                    return result
                if attempts > self.MAX_POLLING:
                    result.update(dict(
                        result='FAILED',
                        msg='Timeout occured while waiting for element'
                    ))
                    return result
                # reset it after each attempt
                self.reset_async_primitives()
                await asyncio.sleep(self.INTERVAL_TIMEOUT)
