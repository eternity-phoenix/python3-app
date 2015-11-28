#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Eternity_Phoenix'

'''handlers for test add_routes(app, "handlers")'''
'''
现在，ORM框架、Web框架和配置都已就绪，我们可以开始编写一个最简单的MVC，把它们全部启动起来。

通过Web框架的@get和ORM框架的Model支持，可以很容易地编写一个处理首页URL的函数：

@get('/')
def index(request):
    users = yield from User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }
'__template__'指定的模板文件是test.html，其他参数是传递给模板的数据，所以我们在模板的根目录templates下创建test.html：
'''
import re, time, json, logging, hashlib, base64, asyncio

from coroweb import get, post
from models import User, Comment, Blog, next_id

from aiohttp import web

@get(['/', '/index', '/home'])
def index(request) :
    #return web.Response(body = b'<h1>Awesome</h1>', content_type = "text/html")
    summary = r'''the quick brown fox jumps over a lazy dog.
    i'm live for study and codes...'''
    blogs = [
        Blog(id = 1, name = 'Test Blog1', summary = summary, created_at = time.time() - 220),
        Blog(id = 2, name = 'Eternity_Phoenix', summary = summary, created_at = time.time() - 1220),
        Blog(id = 3, name = 'lone', summary = summary, created_at = time.time() - 2220)
    ]
    return {
        '__template__' : 'blogs.html',
        'blogs' : blogs
    }

@get('/test')
def test(request) :
    users = yield from User.findAll()
    return {
        '__template__' : 'test.html',
        'users' : users
    }

@get('/api/test/users')
def api_get_users(*args) :
    users = yield from User.findAll(orderBy = 'created_at desc')
    for u in users :
        u.passwd = '********'
    return dict(users = users)

if __name__ == "__main__" :
    r = index(1)
    import json
    rr = json.dumps(r, ensure_ascii = False, default = lambda o : o.__dict__)
    print(rr)
