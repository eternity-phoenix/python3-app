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
from apis import APIError, APIValueError,APIResourceNotFoundError, APIPermissionError, Page

from aiohttp import web
from config import configs

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')
COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

def check_admin(request) :
    if request.__user__ is None or not request.__user__.admin :
        raise APIPermissionError()

def get_page_index(page_str) :
    p = 1
    try :
        p = int(page_str)
    except ValueError as e :
        pass
    if p < 1 :
        p = 1
    return p

def user2cookie(user, max_age) :
    '''
    Generate cookie str by user2cookie
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

def text2html(text) :
    lines = map(lambda s : '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s : s.strip() != '', text.split('\n')))
    return ''.join(lines)

@asyncio.coroutine
def cookie2user(cookie_str) :
    '''
    Parse cookie and load user if cookie is valid
    '''
    if not cookie_str :
        return None
    try :
        L = cookie_str.split('-')
        if len(L) != 3 :
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time() :
            return None
        user = yield from User.find(uid)
        if user is None :
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest() :
            logging.info('///***invalid sha1***///')
            return None
        user.passwd = '********'
        return user
    except Exception as e :
        logging.exception(e)
        return None

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
def api_get_users(request) :
    logging.info('URL return in 56 %s' % request)
    users = yield from User.findAll(orderBy = 'created_at desc')
    for u in users :
        u.passwd = '********'
    return dict(users = users)

@get('/register')
def register(request) :
    return {
        '__template__' : "register.html"
    }

@get('/signin')
def signin(request) :
    return {
        '__template__' : 'signin.html'
    }

@get('/signout')
def signout(request) :
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age = 0, httponly = True)
    logging.info('user signed out')
    return r

@post('/api/authenticate')
def authenticate(*, email, passwd, remember) :
    '''
    LOGIN IN
    '''
    if not email :
        raise APIValueError('email', 'Invalid email')
    if not passwd :
        raise APIValueError('password', 'Invalid password.')
    users = yield from User.findAll('email=?', [email])
    if len(users) == 0 :
        raise APIValueError('email', 'Email not exist.')
    user = user[0]
    #check passwd
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest() :
        raise APIValueError('password', 'Invalid password')
    #authenticate ok, set cookie
    r = web.Response()
    logging.info(remember)
    max_age = 86400 if remember == 'false' else 3600
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age = max_age, httponly = True)
    user.passwd = '********'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii = False).encode('utf-8')
    return r

@post('/api/test/users')
def api_post_users(request) :
    logging.info('URL return in 56 %s' % request)
    users = yield from User.findAll(orderBy = 'created_at desc')
    for u in users :
        u.passwd = '********'
    return dict(users = users)

@post('/api/users')
def api_register_user(*, email, name, password) :
    if not name or not name.strip() :
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email) :
        raise APIValueError('email')
    if not password or not _RE_SHA1.match(password) :
        raise APIValueError('passwd')
    users = yield from User.findAll('email=?', [email])
    if len(users) > 0 :
        raise APIError('register:failed', 'email', 'Email is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, password)
    user = User(id = uid, name = name.strip(), email = email, passwd = hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image = 'http://www.gravatar.com/avatar/%s?d-mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    yield from user.save()
    #make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age = 86400, httponly = True)
    user.passwd = '********'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii = False).encode('utf-8')
    return r

if __name__ == "__main__" :
    r = index(1)
    import json
    rr = json.dumps(r, ensure_ascii = False, default = lambda o : o.__dict__)
    print(rr)
