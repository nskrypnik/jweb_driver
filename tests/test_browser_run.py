import asyncio
import sys
from jweb_driver.browser_driver import BrowserDriver

async def test_browser(driver):
    d = driver
    result = await d.expect_redirect('http://rbcroyalbank.com')
    print(result)
    future = d.wait_for(url=result)
    await future
    await d.wait_for(selector='.info-list')
    result = await d.get_attr('.info-list a', 'href', forall=True)
    print(result)
    if await d.is_element('form[name="jump"] button'):
        print('Button is there')
    await d.click('form[name="jump"] button')
    await d.wait_for(selector='#signInBanner')
    await d.fill_input(selector='#K1', value=sys.argv[1])
    await d.fill_input(selector='#Q1', value=sys.argv[2])
    await d.click('form#rbunxcgi button[type="submit"]')
    await d.wait_for('#creditCards')
    print(await d.get_text('h2'))
    await d.click('#creditCards table a')
    await d.wait_for('.ccadPostedTable')
    print(await d.get_text('.ccadPostedTable tbody tr', forall=True))
    print(await d.get_html('.cardImageCont', forall=True))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    driver = BrowserDriver(loop)
    driver.run()
    loop.create_task(test_browser(driver))
    loop.run_forever()
    driver.shutdown()
