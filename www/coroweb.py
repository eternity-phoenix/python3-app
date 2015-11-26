#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Eternity_Phoenix'

'''DAY5 编写WEB框架'''

'''
在正式开始Web开发前，我们需要编写一个Web框架。

aiohttp已经是一个Web框架了，为什么我们还需要自己封装一个？

原因是从使用者的角度来说，aiohttp相对比较底层，编写一个URL的处理函数需要这么几步：

第一步，编写一个用@asyncio.coroutine装饰的函数：

@asyncio.coroutine
def handle_url_xxx(request):
    pass
第二步，传入的参数需要自己从request中获取：

url_param = request.match_info['key']
query_params = parse_qs(request.query_string)
最后，需要自己构造Response对象：

text = render('template', data)
return web.Response(text.encode('utf-8'))
这些重复的工作可以由框架完成。例如，处理带参数的URL/blog/{id}可以这么写：

@get('/blog/{id}')
def get_blog(id):
    pass
处理query_string参数可以通过关键字参数**kw或者命名关键字参数接收：

@get('/api/comments')
def api_comments(*, page='1'):
    pass
对于函数的返回值，不一定是web.Response对象，可以是str、bytes或dict。

如果希望渲染模板，我们可以这么返回一个dict：

return {
    '__template__': 'index.html',
    'data': '...'
}
因此，Web框架的设计是完全从使用者出发，目的是让使用者编写尽可能少的代码。

编写简单的函数而非引入request和web.Response还有一个额外的好处，就是可以单独测试，否则，
需要模拟一个request才能测试
'''
'''
-------------------------------------------------------
@get和@post

要把一个函数映射为一个URL处理函数，我们先定义@get()：
'''
import asyncio, os, inspect, logging, functools

from urllib import parse

from aiohttp import web

from apis import APIError

def get(path) :
    '''
    Define decorator @get('/path')
    '''
    def decorator(func) :
        @functools.wraps(func)
        def wrapper(*args, **kw) :
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

def post(path) :
    '''
    Define decorator @post('/path')
    '''
    def decorator(func) :
        @functools.wraps(func)
        def wrapper(*args, **kw) :
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator
'''
这样，一个函数通过@get()的装饰就附带了URL信息。

@post与@get定义类似。

定义RequestHandler

URL处理函数不一定是一个coroutine，因此我们用RequestHandler()来封装一个URL处理函数。

RequestHandler是一个类，由于定义了__call__()方法，因此可以将其实例视为函数。

RequestHandler目的就是从URL函数中分析其需要接收的参数，从request中获取必要的参数，调用URL函数，
然后把结果转换为web.Response对象，这样，就完全符合aiohttp框架的要求：
'''
#得到所有的没有默认值的命名关键字参数
def get_required_kw_args(fn) :
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items() :
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty :
            args.append(name)
    return tuple(args)

#得到所有命名关键字参数
def get_named_kw_args(fn) :
    args = []
    params = inspect.signature(fn).parameters
    for name, param in params.items() :
        if param.kind == inspect.Parameter.KEYWORD_ONLY :
            args.append(name)
    return tuple(args)

#命名关键字参数且默认为空
def has_named_kw_args(fn) :
    params = inspect.signature(fn).parameters
    for name, param in params.items() :
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty :
            return True
    return False

#有关键字参数?
def has_var_kw_args(fn) :
    params = inspect.signature(fn).parameters
    for name, param in params.items() :
        if param.kind == inspect.Parameter.VAR_KEYWORD :
            return True
    return False

#有request参数?且接下来的参数必须是位子参数或关键字参数
def has_request_args(fn) :
    sig = inspect.signature(fn)
    params = sig.parameters
    found = False
    for name, param in params.items() :
        if name == 'request' :
            found = True
            continue
        if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD) :
            raise ValueError('request parameters must be the last named parameters in function: %s%s' % (fn.__name__, str(sig)))
    return found

class RequestHandler(object) :
    def __init__(self, app, fn) :
        self._app = app
        self._func = fn
        self._has_request_arg = has_request_args(fn)
        self._has_var_kw_args = has_var_kw_args(fn)
        self._has_named_kw_args = has_named_kw_args(fn)
        self._named_kw_args = get_named_kw_args(fn)
        self._required_kw_args = get_required_kw_args(fn)

    def __str__(self) :
        return str(self.__dict__)

    @asyncio.coroutine
    def __call__(self, request) :
        kw = None
        if self._has_var_kw_args or

if __name__ == '__main__' :
    def test(a, b, c = 0, *args, **kw) :
        pass
    def te(a, b, c = 0, *, d, e = 12, **kw) :
        pass
    def test1(a = 1, *args, **kw) :
        pass
    def test2(a, request, aa, **kw) :
        pass
    print(RequestHandler('111', test))
    print(RequestHandler('111', te))
    print(RequestHandler('111', test1))
    #print(RequestHandler('111', test2))
