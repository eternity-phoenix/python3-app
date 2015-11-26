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

import orm

def index(request) :
    return web.Response(body = b'<h1>Awesome</h1>', content_type = "text/html")

ip = socket.gethostbyname(socket.gethostname())

@asyncio.coroutine
def init(loop) :
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
