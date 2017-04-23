import asyncio
from jweb_driver.browser_driver import BrowserDriver

async def test_browser(driver):
    result = await driver.openurl('http://azhyipmonitor.com/')
    print(result)
    result = await driver.get_attr('.hyip2 a', 'href', forall=False)
    print(result)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    driver = BrowserDriver(loop)
    driver.run()
    loop.create_task(test_browser(driver))
    loop.run_forever()
    driver.shutdown()
