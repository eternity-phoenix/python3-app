#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Eternity_Phoenix'


''' DAY3                ORM'''
'''
在一个Web App中，所有数据，包括用户信息、发布的日志、评论等，都存储在数据库中。
在awesome-python3-webapp中，我们选择MySQL作为数据库。

Web App里面有很多地方都要访问数据库。访问数据库需要创建数据库连接、游标对象，然后执行SQL语句，
最后处理异常，清理资源。这些访问数据库的代码如果分散到各个函数中，势必无法维护，也不利于代码复用。

所以，我们要首先把常用的SELECT、INSERT、UPDATE和DELETE操作用函数封装起来。

由于Web框架使用了基于asyncio的aiohttp，这是基于协程的异步模型。在协程中，
不能调用普通的同步IO操作，因为所有用户都是由一个线程服务的，协程的执行速度必须非常快，
才能处理大量用户的请求。而耗时的IO操作不能在协程中以同步的方式调用，否则，等待一个IO操作时，
系统无法响应任何其他用户。

这就是异步编程的一个原则：一旦决定使用异步，则系统每一层都必须是异步，“开弓没有回头箭”。

幸运的是aiomysql为MySQL数据库提供了异步IO的驱动。

创建连接池

我们需要创建一个全局的连接池，每个HTTP请求都可以从连接池中直接获取数据库连接。
使用连接池的好处是不必频繁地打开和关闭数据库连接，而是能复用就尽量复用。

连接池由全局变量__pool存储，缺省情况下将编码设置为utf8，自动提交事务：
'''
import asyncio, aiomysql

import loggingTools
logger = loggingTools.getLogger('ormlogger')

def log(sql, args = ()) :
    logger.info('SQL: %s' % sql)

@asyncio.coroutine
def create_pool(loop, **kw) :
    logger.info('create database connection pool...')
    global __pool
    __pool = yield from aiomysql.create_pool(
    host = kw.get('host', 'localhost'),
    port = kw.get('port', 3306), #mysql默认端口3306
    user = kw['user'],
    password = kw['password'],
    db = kw['db'],
    charset = kw.get('charset', 'utf8'),
    autocommit = kw.get('autocommit', True),
    maxsize = kw.get('maxsize', 10),
    minsize = kw.get('minsize', 1),
    loop = loop
    )

'''
Select

要执行SELECT语句，我们用select函数执行，需要传入SQL语句和SQL参数：
'''
@asyncio.coroutine
def select(sql, args, size = None) :
    log(sql, args)
    global __pool
    with (yield from __pool) as conn :
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replace('?', '%s'), args or ())
        if size :
            rs = yield from cur.fetchmany(size)
        else :
            rs = yield from cur.fetchall()
        #logger.info((yield from cur.fetchall()))
        yield from cur.close()
        logger.info('rows returned: %s' % len(rs))
        return rs

'''
SQL语句的占位符是?，而MySQL的占位符是%s，select()函数在内部自动替换。
注意要始终坚持使用带参数的SQL，而不是自己拼接SQL字符串，这样可以防止SQL注入攻击。

注意到yield from将调用一个子协程（也就是在一个协程中调用另一个协程）并直接获得子协程的返回结果。

如果传入size参数，就通过fetchmany()获取最多指定数量的记录，否则，通过fetchall()获取所有记录。

Insert, Update, Delete

要执行INSERT、UPDATE、DELETE语句，可以定义一个通用的execute()函数，
因为这3种SQL的执行都需要相同的参数，以及返回一个整数表示影响的行数：
'''

@asyncio.coroutine
def execute(sql, args, autocommit = True) :
    log(sql)
    with (yield from __pool) as conn :
        if autocommit :
            yield from conn.begin()
        try :
            cur = yield from conn.cursor()
            logger.info(str(sql) +'.........' + str(args))
            yield from cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
            yield from cur.close()
            if autocommit :
                yield from conn.commit()
        except BaseException as e :
            if not autocommit :
                yield from conn.rollback()
            raise
        return affected
'''
execute()函数和select()函数所不同的是，cursor对象不返回结果集，而是通过rowcount返回结果数。
'''
'''
ORM

有了基本的select()和execute()函数，我们就可以开始编写一个简单的ORM了。

设计ORM需要从上层调用者角度来设计。

我们先考虑如何定义一个User对象，然后把数据库表users和它关联起来。
代码类似:
from orm import Model, StringField, IntegerField
class User(Model) :
    __table__ = 'users'

    id = IntegerField(primary_key = True)
    name = StringField()

注意到定义在User类中的__table__、id和name是类的属性，不是实例的属性。所以，
在类级别上定义的属性用来描述User对象和表的映射关系，而实例属性必须通过__init__()方法去初始化，所以两者互不干扰：
所以两者互不干扰：

# 创建实例:
user = User(id=123, name='Michael')
# 存入数据库:
user.insert()
# 查询所有User对象:
users = User.findAll()
定义Model

首先要定义的是所有ORM映射的基类Model：

注意到Model只是一个基类，如何将具体的子类如User的映射信息读取出来呢？
答案就是通过metaclass：ModelMetaclass：
'''

'''
Model从dict继承，所以具备所有dict的功能，
同时又实现了特殊方法__getattr__()和__setattr__()，因此又可以像引用普通字段那样写：

>>> user['id']
123
>>> user.id
123
以及Field和各种Field子类：
'''
class Field(object) :
    def __init__(self, name, column_type, primary_key, default) :
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self) :
        return '<%s, %s: %s>' % (self.__class__.__name__, self.column_type, self.name)
#映射varchar的StringField：
class StringField(Field) :
    def __init__(self, name = None, primary_key = False, default = None, ddl = 'varchar(100)') :
        super().__init__(name, ddl, primary_key, default)

class BooleanField(Field) :
    def __init__(self, name = None, default = False) :
        super().__init__(name, 'boolean', False, default)

class IntegerField(Field) :
    def __init__(self, name = None, primary_key = False, default = 0) :
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field) :
    def __init__(self, name = None, primary_key = False, default = 0.0) :
        super().__init__(name, 'real', primary_key, default)

class TextField(Field) :
    def __init__(self, name = None, default = None) :
        super().__init__(name, 'text', False, default)



def create_args_string(num) :
    return ', '.join(['?'] * num)

class ModelMetaclass(type) :
    def __new__(cls, name, bases, attrs) :
        #排除Model类本身
        if name == 'Model' :
            return type.__new__(cls, name, bases, attrs)
        #获取table名称
        tableName = attrs.get('__table__', None) or name
        logger.info('found model: %s (table: %s)' % (name, tableName))
        #获取所有field和主键名
        mappings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items() :
            if isinstance(v, Field) :
                logger.info(' found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key :
                    #找到主键:
                    if primaryKey :
                        #多个主键:
                        raise RuntimeError('Dumlicate primary key for field: %s' % k)
                    primaryKey = k
                else :
                    fields.append(k)
        if not primaryKey :
            raise RuntimeError('Primary Key not found.')
        for k in mappings.keys() :
            attrs.pop(k)
        escaped_fields = list(map(lambda x : '`%s`' % x, fields))
        attrs['__mappings__'] = mappings#保存属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey#主键属性名
        attrs['__fields__'] = fields#除主键外的属性名
         # 构造默认的SELECT, INSERT, UPDATE和DELETE语句:
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda x : '`%s`=?' % (mappings.get(x).name or x), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass = ModelMetaclass) :
    def __init__(self, **kw) :
        if not kw.get(self.__primary_key__, None) :
            if not self.__mappings__[self.__primary_key__].default :
                raise RuntimeError('primary key must has value')
        super(Model, self).__init__(**kw)

    def __getattr__(self, key) :
        try :
            return self[key]
        except KeyError :
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value) :
        self[key] = value

    def getValue(self, key) :
        return getattr(self, key, None)

    def getValueOrDefault(self, key) :
        value = getattr(self, key, None)
        if value is None :
            field = self.__mappings__[key]
            if field.default is not None :
                value = field.default() if callable(field.default) else field.default
                logger.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    @asyncio.coroutine
    def findAll(cls, where = None, args = None, **kw) :
        ' find object by where clause. '
        sql = [cls.__select__]
        if where :
            sql.append('where')
            sql.append(where)
        if args is None :
            args = []
        orderBy = kw.get('orderBy', None)
        if orderBy :
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None :
            sql.append('limit')
            if isinstance(limit, int) :
                sql.append('?')
                sql.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2 :
                sql.append('?, ?')
                args.extend(limit)
                '''2. append() 方法向列表的尾部添加一个新的元素。只接受一个参数。
                3. extend()方法只接受一个列表作为参数，并将该参数的每个元素都添加到原有的列表中。
                '''
            else :
                raise ValueError('Invalid limit value: %s' % str(limit))
                '''
                limit是mysql的语法
                select * from table limit m,n
                其中m是指记录开始的index，从0开始，表示第一条记录
                n是指从第m+1条开始，取n条。
                select * from tablename limit 2,4
                即取出第3条至第6条，4条记录
                '''
        rs = yield from select(' '.join(sql), args)
        return [cls(**r) for r in rs]#DictCursor

    @classmethod
    @asyncio.coroutine
    def findNumber(cls, selectFiled, where = None, args = None) :
        ' find number by select and where '
        sql = ['select %s _num_ from `%s`' % (selectFiled, cls.__table__)]
        if where :
            sql.append('where')
            sql.append(where)
        rs = yield from select(' '.join(sql), args, 1)
        logger.info(',,,,,, %s,,,,,0' % rs )
        if len(rs) == 0 :
            return 0
        #print(rs[0])
        return rs[0]['_num_']

    @classmethod
    @asyncio.coroutine
    def find(cls, pk) :
        ' find object by primary key. '
        rs = yield from select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0 :
            return None
        return cls(**rs[0])


    @asyncio.coroutine
    def save(self) :
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = yield from execute(self.__insert__, args)
        if rows != 1 :
            logger.warn('failed to insert record: affected rows: %s' % rows)

    @asyncio.coroutine
    def update(self) :
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = yield from execute(self.__update__, args)
        if rows != 1 :
            logger.warn('failed to insert record: affected rows: %s' % rows)

    @asyncio.coroutine
    def remove(self) :
        args = [self.getValue(self.__primary_key__)]
        rows = yield from execute(self.__delete__, args)
        if rows != 1 :
            logger.warn('failed to remove by primary key: affected rows: %s' % rows)



'''
这样，任何继承自Model的类（比如User），会自动通过ModelMetaclass扫描映射关系，
并存储到自身的类属性如__table__、__mappings__中。

然后，我们往Model类添加class方法，就可以让所有子类调用class方法：

class Model(dict):

    ...

    @classmethod
    @asyncio.coroutine
    def find(cls, pk):
        ' find object by primary key. '
        rs = yield from select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])
User类现在就可以通过类方法实现主键查找：

user = yield from User.find('123')
往Model类添加实例方法，就可以让所有子类调用实例方法：

class Model(dict):

    ...

    @asyncio.coroutine
    def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = yield from execute(self.__insert__, args)
        if rows != 1:
            logger.warn('failed to insert record: affected rows: %s' % rows)
这样，就可以把一个User实例存入数据库：

user = User(id=123, name='Michael')
yield from user.save()
最后一步是完善ORM，对于查找，我们可以实现以下方法：

findAll() - 根据WHERE条件查找；

findNumber() - 根据WHERE条件查找，但返回的是整数，适用于select count(*)类型的SQL。

以及update()和remove()方法。

所有这些方法都必须用@asyncio.coroutine装饰，变成一个协程。

调用时需要特别注意：

user.save()
没有任何效果，因为调用save()仅仅是创建了一个协程，并没有执行它。一定要用：

yield from user.save()
才真正执行了INSERT操作。
'''
