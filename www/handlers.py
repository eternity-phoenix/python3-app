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
import markdown2

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
def index(request, *, page = 1) :
    #return web.Response(body = b'<h1>Awesome</h1>', content_type = "text/html")
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    page = Page(num, page_index = page_index)
    if num == 0 :
        blogs = []
    else :
        blogs = yield from Blog.findAll(orderBy = 'created_at desc', limit = (page.offset, page.limit))
    return {
        '__template__' : 'blogs.html',
        'blogs' : blogs,
        'page' : page
    }

@get('/blog/{id}')
def get_blog(id) :
    blog = yield from Blog.find(id)
    comments = yield from Comment.findAll('blog_id=?', [id], orderBy = 'created_at desc')
    for c in comments :
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__' : 'blog.html',
        'blog' : blog,
        'comments' : comments
    }
    #except :
        #return web.HTTPBadRequest(body = ('the blog with id %s is not exist!' % id).encode('utf-8'))

@get('/manage/')
def manage(request) :
    return 'redirect:/manage/comments'

@get('/manage/comments')
def manage_comments(request, *, page = '1') :
    return {
        '__template__' : 'manage_comments.html',
        'page_index' : get_page_index(page)
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
    user = users[0]
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
    if not str(name).strip() :
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
    user = User(id = uid, name = str(name).strip(), email = email, passwd = hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image = 'http://www.gravatar.com/avatar/%s?d-mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    yield from user.save()
    #make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age = 86400, httponly = True)
    user.passwd = '********'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii = False).encode('utf-8')
    return r

@post('/api/comments/{id}/delete')
def api_delete_comments(id, request) :
    check_admin(request)
    c = yield from Comment.find(id)
    if c is None :
        raise APIResourceNotFoundError('Comment')
    yield from c.remove()
    return dict(id = id)

@get('/api/users')
def api_get_users(request, *, page = 1) :
    page_index = get_page_index(page)
    num = yield from User.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0 :
        return dict(page = p, users = ())
    users = yield from User.findAll(orderBy = 'created_at desc', limit = (p.offset, p.limit))
    for u in users :
        u.passwd = '********'
    return dict(page = p, users = users)


@get('/manage/blogs/create')
def manage_create_blog(request) :
    return {
        '__template__' : 'manage_blog_edit.html',
        'id' : '',
        'action' : '/api/blogs'
    }

@get('/manage/blogs/edit')
def manage_edit_blog(request, *, id) :
    return {
        '__template__' : 'manage_blog_edit.html',
        'id' : id,
        'action' : '/api/blogs/%s' % id
    }

@get('/manage/users')
def manage_users(request, *, page = 1) :
    return {
        '__template__' : 'manage_users.html',
        'page_index' : get_page_index(page)
    }

@get('/api/comments')
def api_comments(request, *, page = 1) :
    page_index = get_page_index(page)
    num = yield from Comment.findNumber('count(id)')
    p = Page(num, page_index = page_index)
    if num == 0 :
        return dict(page = p, comments = ())
    comments = yield from Comment.findAll(orderBy = 'created_at desc', limit = (p.offset, p.limit))
    return dict(page = p, comments = comments)

@get('/api/blogs')
def api_blogs(*, page = 1) :
    page_index = get_page_index(page)
    num = yield from Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0 :
        return dict(page = p, blogs = ())
    blogs = yield from Blog.findAll(orderBy = 'created_at desc', limit = (p.offset, p.limit))
    return dict(page = p, blogs = blogs)

@post('/api/blogs/{id}/comments')
def api_create_comments(id, request, *, content) :
    user = request.__user__
    if user is None :
        raise APIPermissionError('Please signin first.')
    if not str(content).strip() :
        raise APIValueError('content')
    blog = yield from Blog.find(id)
    if blog is None :
        raise APIResourceNotFoundError('Blog')
    comment = Comment(blog_id = id, user_id = user.id, user_name = user.name, user_image = user.image, content = str(content).strip())
    yield from comment.save()
    return comment

@get('/manage/blogs')
def manage_blogs(*, page = 1) :
    '''
    模板页面首先通过API：GET /api/blogs?page=?拿到Model：
    '''
    return {
        '__template__' : 'manage_blogs.html',
        'page_index' : get_page_index(page)
    }

@post('/api/blogs')
def api_create_blog(request, *, name, summary, content) :
    check_admin(request)
    logging.info('create blog')
    if not str(name).strip() :
        raise APIValueError('name', 'name cannot be empty.')
    if not str(summary).strip() :
        raise APIValueError('summary', 'summary cannot be empty.')
    if not str(content).strip() :
        raise APIValueError('strip', 'strip cannot be empty.')
    blog = Blog(user_id = request.__user__.id, user_name = request.__user__.name, user_image = request.__user__.image, name = str(name).strip(), summary = summary, content = str(content).strip())
    yield from blog.save()
    return blog

@get('/api/blogs/{id}')
def api_get_blog(request, *, id) :
    blog = yield from Blog.find(id)
    return blog

@post('/api/blogs/{id}')
def api_update_blog(id, request, *, name, summary, content, created_at) :
    check_admin(request)
    blog = yield from Blog.find(id)
    if not str(name).strip() :
        raise APIValueError('name', 'name cannot be empty.')
    if not str(summary).strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not str(content).strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = str(name).strip()
    blog.summary = str(summary).strip()
    blog.content = str(content).strip()
    try :
        blog.created_at = float(created_at)
    except :
        blog.created_at = created_at
    yield from blog.update()
    return blog

@post('/api/blogs/{id}/delete')
def api_delete_blog(request, *, id) :
    check_admin(request)
    blog = yield from Blog.find(id)
    yield from blog.remove()
    return dict(id = id)

if __name__ == "__main__" :
    r = index(1)
    import json
    rr = json.dumps(r, ensure_ascii = False, default = lambda o : o.__dict__)
    print(rr)
