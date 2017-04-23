
class LoadHandlerWrapper(object):

    def __init__(self, driver):
        self.driver = driver

    def OnLoadEnd(self, browser, frame, http_code):
        self.driver.on_load_end(browser, frame, http_code)


class RequestHandlerWrapper(object):

    def __init__(self, driver):
        self.driver = driver

    def OnResourceRedirect(self, **kw):
        self.driver.on_resource_redirect(**kw)
