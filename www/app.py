#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Eternity_Phoenix'

'''                 DAY2                         编写APP骨架'''

'''
由于我们的Web App建立在asyncio的基础上，因此用aiohttp写一个基本的app.py：
'''

import sys
sys.path.append('/home/eternity-phoenix/.local/lib/python3.5/site-packages')
#由于server的模块安装位置不当,请无视

import logging; logging.basicConfig(level = logging.INFO)

import asyncio, os, json, time, socket
from datetime import datetime

from aiohttp import web
from jinja2 import Environment, FileSystemLoader

from coroweb import add_routes, add_static
import orm
from config import configs
from handlers import COOKIE_NAME, cookie2user
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
    logging.info('init_jinja2 complete!')

@asyncio.coroutine
def logger_factory(app, handler) :
    @asyncio.coroutine
    def logger(request) :
        logging.info('Request: %s %s' % (request.method, request.path))
        #yield from asyncio.sleep(0.3)
        return (yield from handler(request))
    return logger

@asyncio.coroutine
def auth_factory(app, handler) :
    @asyncio.coroutine
    def auth(request) :
        logging.info('check user : %s %s' % (request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str :
            user = yield from cookie2user(cookie_str)
            if user :
                logging.info('set current user: %s' % user.email)
                request.__user__ = user
        if request.path.startswith('/manage/') and (request.__user__ is None or not request.__user__.admin) :
            return web.HTTPFound('/signin')
        logging.info('authenticate finished!')
        return (yield from handler(request))
    return auth

@asyncio.coroutine
def data_factory(app, handler) :
    @asyncio.coroutine
    def parse_data(request) :
        '''
        移动APP预留接口
        '''
        logging.info('parse_data in line 98')
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
        logging.info('Response handler... (%s)...' % request) #% (handler.__name__, str(dir((app)))))
        #logging.info(dir(handler.__call__), type(handler.__call__))
        r = yield from handler(request)
        #logging.info(type(r), r)
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
            logging.info(r)
            template = r.get('__template__', None)
            if template is None :
                resp = web.Response(body = json.dumps(r, ensure_ascii = False, default = lambda o : o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else :
                try :
                    r['__user__'] = request.__user__
                except :
                    print('**********\r\nwarning\r\n**********')
                #print(dir(request))
                resp = web.Response(body = app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and t < 600 :
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2 :
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600 :
                return web.Response(t, str(m))
        #default:
        resp = web.Response(body = str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp
    return response

def datetime_filter(t) :
    delta = int(time.time() - t)
    if delta < 60 :
        return u'1分钟前'
    if delta < 3600 :
        return u'%s分钟前' % (delta // 60)
    if delta < 3600 * 24 :
        return u'%s小时前' % (delta // 3600)
    if delta < 3600 * 24 * 7 :
        return u'%s天前' % (delta // (3600 * 24))
    if delta < 3600 * 24 * 30 :
        return u'%s周前' % (delta // (3600 * 24 * 7))
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


ip = socket.gethostbyname(socket.gethostname())



'''
最后，在app.py中加入middleware、jinja2模板和自注册的支持：
'''
@asyncio.coroutine
def init(loop) :
    yield from orm.create_pool(loop = loop, **configs.db)
    app = web.Application(loop = loop, debug = True, middlewares = [
        logger_factory, response_factory, auth_factory
    ])
    init_jinja2(app, filters = dict(datetime = datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)

    logging.info('init complete!')

    #print(ip)
    r = input('run at local(1) or temp test at web(2)?')
    if r == '1' :
        _ip = '127.0.0.1'
        port = 9000
    else :
        port = 80
        _ip = ip
    srv = yield from loop.create_server(app.make_handler(), _ip, port)
    logging.info('server started at http://%s:80...' % ip)
    return srv

if __name__ == '__main__' :
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    loop.run_forever()

'''
运行python app.py，Web App将在9000端口监听HTTP请求，并且对首页/进行响应：
'''
