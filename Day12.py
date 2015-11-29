#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Eternity_Phoenix'

'''             day12       MANAGE BLOG'''
'''
MVVM模式不但可用于Form表单，在复杂的管理页面中也能大显身手。例如，分页显示Blog的功能，我们先把后端代码写出来：

在apis.py中定义一个Page类用于存储分页信息：

在handlers.py中实现API：

@get('/api/blogs')

管理页面：

@get('/manage/blogs')

模板页面首先通过API：GET /api/blogs?page=?拿到Model：

}
然后，通过Vue初始化MVVM：

View的容器是#vm，包含一个table，我们用v-repeat可以把Model的数组blogs直接变成多行的<tr>：

往Model的blogs数组中增加一个Blog元素，table就神奇地增加了一行；把blogs数组的某个元素删除，
table就神奇地减少了一行。所有复杂的Model-View的映射逻辑全部由MVVM框架完成，
我们只需要在HTML中写上v-repeat指令，就什么都不用管了。

可以把v-repeat="blog: blogs"看成循环代码，所以，可以在一个<tr>内部引用循环变量blog。
v-text和v-attr指令分别用于生成文本和DOM节点属性。

完整的Blog列表页如下：
'''
