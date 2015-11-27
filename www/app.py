#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Eternity_Phoenix'

'''                 DAY2                         编写APP骨架'''

'''
由于我们的Web App建立在asyncio的基础上，因此用aiohttp写一个基本的app.py：
'''
import logging; logging.basicConfig(level = logging.INFO)

import asyncio, os, json, time, socket
from datetime import datetime

from aiohttp import web
from jinja2 import Environment, FileSystemLoader

from coroweb import add_routes, add_static
import orm


'''
middleware

middleware是一种拦截器，一个URL在被某个函数处理前，可以经过一系列的middleware的处理。

一个middleware可以改变URL的输入、输出，甚至可以决定不继续处理而直接返回。
middleware的用处就在于把通用的功能从每个URL处理函数中拿出来，集中放到一个地方。例如，
一个记录URL日志的logger可以简单定义如下：

@asyncio.coroutine
def logger_factory(app, handler):
    @asyncio.coroutine
    def logger(request):
        # 记录日志:
        logging.info('Request: %s %s' % (request.method, request.path))
        # 继续处理请求:
        return (yield from handler(request))
    return logger
而response这个middleware把返回值转换为web.Response对象再返回，以保证满足aiohttp的要求：

@asyncio.coroutine
def response_factory(app, handler):
    @asyncio.coroutine
    def response(request):
        # 结果:
        r = yield from handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            ...
有了这些基础设施，我们就可以专注地往handlers模块不断添加URL处理函数了，可以极大地提高开发效率。
'''
def init_jinja2(app, **kw) :
    logging.info('init jinja2...')
    options = dict(
        autoescape = kw.get('autoescape', True),
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None :
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader = FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None :
        for name, f in filters.items() :
            env.filters[name] = f
    app['__templating__'] = env

@asyncio.coroutine
def logger_factory(app, handler) :
    @asyncio.coroutine
    def logger(request) :
        logging.info('Request: %s %s' % (request.method, request.path))
        #yield from asyncio.sleep(0.3)
        return (yield from handler(request))
    return logger

@asyncio.coroutine
def data_factory(app, handler) :
    @asyncio.coroutine
    def parse_data(request) :
        if request.method == 'POST' :
            if request.content_type.lower().startswith('application/json') :
                request.__data__ = yield from request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.lower().startswith('application/x-www-form-urlencoded') :
                request.__data__ = yield from request.post()
                logging.info('request from : %s' % str(request.__data__))
        return (yield from handler(request))
    return parse_data

@asyncio.coroutine
def response_factory(app, handler) :
    @asyncio.coroutine
    def response(request) :
        logging.info('Response handler... (%s)...(%s)' % (andler, app))
        r = yield from handler(request)
        if isinstance(r, web.StreamResponse) :
            return r
        if isinstance(r, bytes) :
            resp = web.Response(body = r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str) :
            if r.startswith('redirect:') :
                return web.HTTPFound(r[9 :])
            resp = web.Response(body = r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict) :
            template = r.get('__template__', None)
            if template is None :
                resp = web.Response(body = json.dumps(r, ensure_ascii = False, default = lambda o : o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else :
                r['__user__'] = request.__user__
                resp = web.Response(body = app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
def index(request) :
    return web.Response(body = b'<h1>Awesome</h1>', content_type = "text/html")

ip = socket.gethostbyname(socket.gethostname())



'''
最后，在app.py中加入middleware、jinja2模板和自注册的支持：
'''
@asyncio.coroutine
def init(loop) :
    yield from orm.create_pool(loop = loop, host = 'localhost', port = 3306, user = 'www-data', password = 'www-data', db = 'awesome')
    app = web.Application(loop = loop)
    app.router.add_route('GET', '/', index)
    srv = yield from loop.create_server(app.make_handler(), ip, 80)
    logging.info('server started at http://%s:80...' % ip)
    return srv

if __name__ == '__main__' :
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()

'''
运行python app.py，Web App将在9000端口监听HTTP请求，并且对首页/进行响应：
'''
