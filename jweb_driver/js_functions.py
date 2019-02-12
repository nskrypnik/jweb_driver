from string import Template

# js functions

JS_CODE_METHODS = {
'js_get_attr_all': """
    var attr_values = []
    document.querySelectorAll('${selector}').forEach(function (node) {
        attr_values.push(node.getAttribute('${attr}'))
    })
    return attr_values
""",

'js_get_attr': """
    var node = document.querySelector('${selector}')
    return node.getAttribute('${attr}')
""",

'js_is_element': """
    return document.querySelectorAll('${selector}').length
""",

'js_click': """
    document.querySelector('${selector}').click()
""",

'js_fill_input': """
    document.querySelector('${selector}').value = '${value}'
""",

'js_fill_input_all': """
    document.querySelectorAll('${selector}').forEach(function (node) {
        node.value = '${value}'
    })
""",

'js_get_text': """
    var node = document.querySelector('${selector}')
    if (node) {
        return node.textContent
    }
""",

'js_get_text_all': """
    var result = []
    document.querySelectorAll('${selector}').forEach(function (node) {
        result.push(node.textContent)
    })
    return result
""",

'js_get_html': """
    var node = document.querySelector('${selector}')
    if (node) {
        return node.innerHTML
    }
""",

'js_get_html_all': """
    var result = []
    document.querySelectorAll('${selector}').forEach(function (node) {
        result.push(node.innerHTML)
    })
    return result
""",

'js_get_location': """
    return window.location.href
"""
}

def js_execute_code(func_code, browser):
    # wrap js code into the try-catch statement and function to be execute
    # inside
    code = 'try {\n'
    code += 'res = (function () {\n%s\n})()\n' % func_code
    code += 'py_data_callback(res)\n'
    code += '} catch (e) {\n'
    code += 'py_handle_exception(e)\n'
    code += '}'
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

@js_function
def js_is_element(browser, **kw):
    pass

@js_function
def js_click(browser, **kw):
    pass

@js_function
def js_fill_input(browser, **kw):
    pass

@js_function
def js_get_text(browser, **kw):
    pass

@js_function
def js_get_html(browser, **kw):
    pass

@js_function
def js_get_location(browser, **kw):
    pass
