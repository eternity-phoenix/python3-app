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
