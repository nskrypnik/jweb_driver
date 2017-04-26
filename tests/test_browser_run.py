import asyncio
from jweb_driver.browser_driver import BrowserDriver

async def test_browser(driver):
    globals().update(dict(
        wait_for=driver.wait_for,
        get_attr=driver.get_attr,
        click=driver.click,
        is_element=driver.is_element,
        open_url=driver.open_url
    ))
    result = await open_url('http://rbcroyalbank.com')
    print(result)
    await wait_for(selector='.info-list')
    result = await get_attr('.info-list a', 'href', forall=True)
    print(result)
    if await is_element('form[name="jump"] button'):
        print('Button is there')
    await click('form[name="jump"] button')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    driver = BrowserDriver(loop)
    driver.run()
    loop.create_task(test_browser(driver))
    loop.run_forever()
    driver.shutdown()
