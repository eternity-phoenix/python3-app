#!/usr/bin/env python2
# -*- coding: utf-8 -*-

__author__ = 'Eternity_Phoenix'
#注意,是python2;且保存的文件名必须是fabfile.py

import os, re
from datetime import datetime

# 导入Fabric API:
from fabric.api import *

# 服务器登录用户名:
env.user = 'eternity-phoenix'
# sudo用户为root:
env.sudo_user = 'root'
# 服务器地址，可以有多个，依次部署:
env.hosts = ['192.168.153.130']

# 服务器MySQL用户名和口令:
db_user = 'www-data'
db_password = 'www-data'

_TAR_FILE = 'dist-awesome.tar.gz'

_REMOTE_TMP_TAR = '/tmp/%s' % _TAR_FILE

_REMOTE_BASE_DIR = '/srv/awesome'


def _current_path() :
    return os.path.abspath('.')

def _now() :
    return datetime.now().strftime('%y-%m-%d_%H.%M.%S')


def backup() :
    '''
    Dump entire database on server and backup to local.
    '''
    dt = _now()
    f = 'backup-awesome-%s.sql' % dt
    with cd('/tmp') :
        run('mysqldump --user=%s --password=%s --skip-opt --add-drop-table --default-character-set=utf8 --quick awesome > %s' % (db_user, db_password, f))
        run('tar -czvf %s.tar.gz %s' % (f, f))
        get('%s.tar.gz' % f, '%s/backup/' % _current_path())
        run('rm -f %s' % f)
        run('rm -f %s.tar.gz' % f)

def build() :
    '''
    Build dist package.
    '''
    includes = ['static', 'templates', 'transwarp', 'favicon.ico', '*.py']
    excludes = ['test', '.*', '*.pyc', '*.pyo']
    local('rm -f dist/%s' % _TAR_FILE)
    with lcd(os.path.join(_current_path(), 'www')) :
        cmd = ['tar', '--dereference', '-czvf', '../dist/%s' % _TAR_FILE]
        cmd.extend(['--exclude=\'%s\'' % ex for ex in excludes])
        cmd.extend(includes)
        local(' '.join(cmd))

def deploy() :
    newdir = 'www-%s' % _now()
    #删除已有的tar文件:
    run('rm -f %s' % _REMOTE_TMP_TAR)
    # 上传新的tar文件:
    put('dist/%s' % _TAR_FILE, _REMOTE_TMP_TAR)
    # 创建新目录:
    with cd(_REMOTE_BASE_DIR) :
        sudo('mkdir %s' % newdir)
    # 解压到新目录:
    with cd('%s/%s' % (_REMOTE_BASE_DIR, newdir)):
        sudo('tar -xzvf %s' % _REMOTE_TMP_TAR)
    # 重置软链接:
    with cd(_REMOTE_BASE_DIR) :
        sudo('rm -f www')
        sudo('ln -s %s www' % newdir)
        #chown将指定文件的拥有者改为指定的用户或组，
        sudo('chown eternity-phoenix:eternity-phoenix www')
        sudo('chown -R eternity-phoenix:eternity-phoenix %s' % newdir)
    # 重启Python服务和nginx服务器:
    with settings(warn_only = True) :
        sudo('supervisorctl stop awesome')
        sudo('supervisorctl start awesome')
        sudo('/etc/init.d/nginx reload')

RE_FILES = re.compile('\s+')

def rollback() :
    '''
    rollback to previous version
    '''
    with cd(_REMOTE_BASE_DIR) :
        r = run('ls -p')
        #print('\r\n', r, type(r), '\r\n')
        files = [s[: -1] for s in RE_FILES.split(r) if s.startswith('www-') and s.endswith('/')]
        files.sort(cmp = lambda s1, s2 : 1 if s1 < s2 else -1)#倒序6,5,4,3,2,1
        r = run('ls -l www')
        #print(files)
        #print('\r\n', r, '\r\n')
        #print('\r\n', files, '\r\n')
        ss = r.split(' ->')
        if len(ss) != 2 :
            print('ERROR: \'www\' is not a symbol link.')
            return
        current = ss[1].strip()
        print('Found current symbol link points to: %s\n' % current)
        try :
            #print(type(files[0]), type(current))
            print(current)
            index = files.index(current)
        except ValueError, e :#python2用法
            print('ERROR: symbol link is invalid.')
            return
        if len(files) == index + 1 :
            print('ERROR: already the oldest version.')
            return
        old = files[index + 1]
        print('=========================================')
        for f in files :
            if f == current :
                print('    Current ----> %s' % current)
            elif f == old :
                print('  Rollback to ----> %s' % old)
            else :
                print('        %s' % f)
        print('=========================================')
        print('')
        yn = raw_input('continue? y/N')
        if yn != 'y' and yn != 'Y' :
            print('Rollback ancelled.')
            return
        print('Start rollback...')
        sudo('rm -f www')
        sudo('ln -s %s www' % old)
        sudo('chown eternity-phoenix:eternity-phoenix www')
        with settings(warn_only = True) :
            sudo('supervisorctl stop awesome')
            sudo('supervisorctl start awesome')
            sudo('/etc/init.d/nginx reload')
        print('ROLLBACK OK.')

def restore2local() :
    '''
    Restore db to local
    '''
    backup_dir = os.path.join(_current_path(), 'backup')
    fs = os.listdir(backup_dir)
    files = [f for f in fs if f.startswith('backup-') and f.endswith('.sql.tar.gz')]
    files.sort(cmp = lambda s1, s2 : 1 if s1 < s2 else -1)
    if len(files) == 0 :
        print('No backup files found.')
        return
    print('Found %s backup files:' % len(files))
    print('==================================================')
    n = 0
    for f in files :
        print ('%s: %s' % (n, f))
        n = n + 1
    print ('==================================================')
    print ('')
    try :
        num = int(raw_input('Restore file number.'))
    except ValueError :
        print('invalid file number index.')
        return
    restore_file = files[num]
    yn = raw_input('Restore file %s: %s? y/N ' % (num, restore_file))
    if yn != 'y' and yn != 'Y' :
        print('Restore cancelled.')
        return
    print('Start restore to local database...')
    p = raw_input('Input mysql root password: ')
    sqls = [
        'drop database if exists awesome;',
        'create database awesome;',
        'grant select, insert, update on awesome.* to \'%s\'@\'localhost\' identified by \'%s\';' % (db_user, db_password)
    ]
    for sql in sqls :
        local(r'mysql -uroot -p%s -e "%s"' % (p, sql))
    with lcd(backup_dir) :
        local('tar zxvf %s' % restore_file)
    local(r'mysql -uroot -p%s awesome < backup/%s' % (p, restore_file[: -7]))
    with lcd(backup_dir) :
        local('rm -f %s' % restore_file[: -7])
