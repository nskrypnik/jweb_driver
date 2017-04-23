from string import Template

# js functions

JS_CODE_METHODS = {
'js_get_attr_all': """

    var attr_values = []
    document.querySelectorAll('${selector}').forEach(function (node) {
        attr_values.push(node.getAttribute('${attr}'))
    })

    if (!attr_values.length) {
        return {
            result: 'failure',
            msg: 'Elements aren\\'t found'
        }
    }

    return {
        result: 'success',
        data: attr_values
    }
""",

'js_get_attr': """

    var node = document.querySelector('${selector}')
    if (!node) {
        return {
            result: 'failure',
            msg: 'Elements aren\\'t found'
        }
    }
    return {
        result: 'success',
        data: node.getAttribute('${attr}')
    }
"""
}

def js_execute_code(code, browser):
    code = 'res = (function () {\n%s\n})()\n' % code
    code += 'py_data_callback(res)'
    browser.ExecuteJavascript(code)


def js_function(func):
    def wrapper(browser, **kw):
        func_name = func.__name__
        if kw.get('forall', False):
            func_name += '_all'
        code = Template(JS_CODE_METHODS[func_name]).safe_substitute(kw)
        js_execute_code(code, browser)
    return wrapper


@js_function
def js_get_attr(browser, **kw):
    pass
