#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Eternity_Phoenix'


import logging#; logging.basicConfig(level = logging.INFO)
import os, os.path

logger = logging.getLogger('mylogger')
logger.setLevel(logging.INFO)

logger2 = logging.getLogger('ormlogger')
logger2.setLevel(logging.DEBUG)

# 创建一个handler，用于写入日志文件
path = os.path.join(os.path.split(os.path.realpath(__file__))[0], 'log')
if not os.path.exists(path) :
    os.makedirs(path)
if os.path.isfile(path) :
    os.remove(path)
    os.makedirs(path)


fh = logging.FileHandler('./log/awesome.log')
fh.setLevel(logging.INFO)
# 再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# 定义handler的输出格式
formatter =logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# 给logger添加handler

logger.addHandler(fh)
logger.addHandler(ch)
logger2.addHandler(fh)
logger2.addHandler(ch)

def getLogger(name = None) :
    return logging.getLogger(name)
