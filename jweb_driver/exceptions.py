
class OperationTimeout(Exception):

    def __init__(self, message):
        self.message = message


class ElementNotFound(Exception):

    def __init__(self, selector):
        self.message = 'Element is not found with selector "%s"' % selector


class JavaScriptError(Exception):

    def __init__(self, js_error):
        self.js_error = js_error
        self.message = js_error['message']
