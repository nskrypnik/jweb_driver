import asyncio
import sys
from cefpython3 import cefpython as cef
from .browser_driver import BrowserDriver, BROWSER_LOOP_DELAY

class DriversPool:
    '''A pool of browser drivers
    '''

    def __init__(self, number, loop):
        '''Constructor, creates a number of browser drivers specified in
           number parameter
        '''
        self.loop = loop
        self._init_cef()
        self.drivers = []
        for i in range(number):
            self.drivers.append(BrowserDriver(loop, cef))

    def _init_cef(self):
        sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
        cef.Initialize({
            'log_severity': cef.LOGSEVERITY_DISABLE,
            'windowless_rendering_enabled': True,
            'debug': False
        })

    def run(self):
        '''Start all browser drivers in pool
        '''
        self.loop.create_task(self.browser_message_loop())
        for driver in self.drivers:
            driver.is_browser_running = True

    def shutdown(self):
        cef.shutdown()
        for driver in self.drivers:
            driver.is_browser_running = False

    async def browser_message_loop(self):
        '''Run browser message loop within asyncio loop
        '''
        while True:
            cef.MessageLoopWork()
            await asyncio.sleep(BROWSER_LOOP_DELAY)
