import asyncio
from jweb_driver.browser_driver import BrowserDriver

async def test_browser(driver):
    result = await driver.open_url('http://rbcroyalbank.com')
    print(result)
    await driver.wait_for(selector='.info-list')
    result = await driver.get_attr('.info-list a', 'href', forall=True)
    print(result)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    driver = BrowserDriver(loop)
    driver.run()
    loop.create_task(test_browser(driver))
    loop.run_forever()
    driver.shutdown()
