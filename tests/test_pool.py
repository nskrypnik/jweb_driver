import asyncio
import sys
from jweb_driver.drivers_pool import DriversPool


async def test_pool(driver, url):
    print(await driver.open_url(url))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    pool = DriversPool(20, loop)
    pool.run()
    loop.create_task(test_pool(pool.drivers[0], 'http://google.com'))
    loop.create_task(test_pool(pool.drivers[1], 'http://yahoo.com'))
    loop.create_task(test_pool(pool.drivers[2], 'http://bing.com'))
    loop.create_task(test_pool(pool.drivers[3], 'http://yandex.ru'))
    loop.create_task(test_pool(pool.drivers[4], 'http://fb.com'))
    loop.create_task(test_pool(pool.drivers[5], 'http://yp.com'))
    loop.create_task(test_pool(pool.drivers[6], 'http://github.com'))
    loop.create_task(test_pool(pool.drivers[7], 'http://bitbucket.com'))
    loop.create_task(test_pool(pool.drivers[8], 'http://microsoft.com'))
    loop.create_task(test_pool(pool.drivers[9], 'http://uber.com'))
    loop.create_task(test_pool(pool.drivers[10], 'http://airbnb.com'))
    loop.create_task(test_pool(pool.drivers[11], 'http://expedia.com'))
    loop.create_task(test_pool(pool.drivers[12], 'http://craigslist.com'))
    loop.create_task(test_pool(pool.drivers[13], 'http://slack.com'))
    loop.create_task(test_pool(pool.drivers[14], 'http://apple.com'))
    loop.create_task(test_pool(pool.drivers[15], 'http://godaddy.com'))
    loop.create_task(test_pool(pool.drivers[16], 'http://skype.com'))
    loop.create_task(test_pool(pool.drivers[17], 'http://wordpress.com'))
    loop.create_task(test_pool(pool.drivers[19], 'http://amazon.com'))
    loop.create_task(test_pool(pool.drivers[15], 'http://booking.com'))
    loop.run_forever()
    driver.shutdown()
