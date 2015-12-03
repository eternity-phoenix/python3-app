#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Eternity_Phoenix'


'''
作为一个合格的开发者，在本地环境下完成开发还远远不够，我们需要把Web App部署到远程服务器上，这样，
广大用户才能访问到网站。

很多做开发的同学把部署这件事情看成是运维同学的工作，这种看法是完全错误的。首先，最近流行DevOps理念，
就是说，开发和运维要变成一个整体。其次，运维的难度，其实跟开发质量有很大的关系。代码写得垃圾，
运维再好也架不住天天挂掉。最后，DevOps理念需要把运维、监控等功能融入到开发中。
你想服务器升级时不中断用户服务？那就得在开发时考虑到这一点。

下面，我们就来把awesome-python3-webapp部署到Linux服务器。

搭建Linux服务器

要部署到Linux，首先得有一台Linux服务器。要在公网上体验的同学，
可以在Amazon的AWS申请一台EC2虚拟机（免费使用1年），或者使用国内的一些云服务器，
一般都提供Ubuntu Server的镜像。想在本地部署的同学，请安装虚拟机，推荐使用VirtualBox。

我们选择的Linux服务器版本是Ubuntu Server 14.04 LTS，原因是apt太简单了。
如果你准备使用其他Linux版本，也没有问题。

Linux安装完成后，请确保ssh服务正在运行，否则，需要通过apt安装：

$ sudo apt-get install openssh-server
有了ssh服务，就可以从本地连接到服务器上。建议把公钥复制到服务器端用户的.ssh/authorized_keys中，这样，
就可以通过证书实现无密码连接。
--------------------------------------------------------------------------
ssh-keygen  产生公钥与私钥对.
ssh-copy-id 将本机的公钥复制到远程机器的authorized_keys文件中
，ssh-copy-id也能让你有到远程机器的home, ~./ssh , 和 ~/.ssh/authorized_keys的权利

第一步:在本地机器上使用ssh-keygen产生公钥私钥对
jsmith@local-host$ [Note: You are on local-host here]
jsmith@local-host$ ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/home/jsmith/.ssh/id_rsa):[Enter key]直接enter,不输入任何
Enter passphrase (empty for no passphrase): [Press enter key]
Enter same passphrase again: [Pess enter key]
Your identification has been saved in /home/jsmith/.ssh/id_rsa.
Your public key has been saved in /home/jsmith/.ssh/id_rsa.pub.
The key fingerprint is:
33:b3:fe:af:95:95:18:11:31:d5:de:96:2f:f2:35:f9 jsmith@local-host
第二步:用ssh-copy-id将公钥复制到远程机器中
jsmith@local-host$ ssh-copy-id -i ~/.ssh/id_rsa.pub remote-host
jsmith@remote-host's password:
Now try logging into the machine, with "ssh 'remote-host'", and check in:
.ssh/authorized_keys
to make sure we haven't added extra keys that you weren't expecting.
注意: ssh-copy-id 将key写到远程机器的 ~/ .ssh/authorized_key.文件中
第三步: 登录到远程机器不用输入密码
jsmith@local-host$ ssh remote-host
Last login: Sun Nov 16 17:22:33 2008 from 192.168.1.2
[Note: SSH did not ask for password.]
jsmith@remote-host$ [Note: You are on remote-host here]
=----------------------------------------------------------------------

部署方式

利用Python自带的asyncio，我们已经编写了一个异步高性能服务器。但是，我们还需要一个高性能的Web服务器，
这里选择Nginx，它可以处理静态资源，同时作为反向代理把动态请求交给Python代码处理。这个模型如下：

nginx-awesome-mysql

Nginx负责分发请求：

browser-----------nginx------------awesome
                   |          |        |
           url=/static/      url=/     /srv/awesome/www
                    |
                    /srv/awesome/www/static
在服务器端，我们需要定义好部署的目录结构：

/
+- srv/
   +- awesome/       <-- Web App根目录
      +- www/        <-- 存放Python源码
      |  +- static/  <-- 存放静态资源文件
      +- log/        <-- 存放log
在服务器上部署，要考虑到新版本如果运行不正常，需要回退到旧版本时怎么办。
每次用新的代码覆盖掉旧的文件是不行的，需要一个类似版本控制的机制。由于Linux系统提供了软链接功能，
所以，我们把www作为一个软链接，它指向哪个目录，哪个目录就是当前运行的版本：

而Nginx和gunicorn的配置文件只需要指向www目录即可。

Nginx可以作为服务进程直接启动，但gunicorn还不行，所以，Supervisor登场！Supervisor是一个管理进程的工具，
可以随系统启动而启动服务，它还时刻监控服务进程，如果服务进程意外退出，Supervisor可以自动重启服务。

总结一下我们需要用到的服务有：

Nginx：高性能Web服务器+负责反向代理；

Supervisor：监控服务进程的工具；

MySQL：数据库服务。

在Linux服务器上用apt可以直接安装上述服务：

$ sudo apt-get install nginx supervisor python3 mysql-server
然后，再把我们自己的Web App用到的Python库安装了：

$ sudo pip3 install jinja2 aiomysql aiohttp
在服务器上创建目录/srv/awesome/以及相应的子目录。

在服务器上初始化MySQL数据库，把数据库初始化脚本schema.sql复制到服务器上执行：
---------------------------------------------------------------
三，复制文件或目录命令：
  复制文件：
  （1）将本地文件拷贝到远程
  scp 文件名用户名@计算机IP或者计算机名称:远程路径


  本地192.168.1.8客户端
  scp /root/install.* root@192.168.1.12:/usr/local/src


  （2）从远程将文件拷回本地
  scp 用户名@计算机IP或者计算机名称:远程路径 文件名本地路径



  本地192.168.1.8客户端取远程服务器12、11上的文件
  scp



  本地机:X.X.29.12        远程机：X.X.29.18   远程机用户：aaron
  要求将本地机上的/www/xinpindao     复制到远程机的/tmp/www %
  scp  -r   /www/xinpindao    aaron@X.X.29.18:/tmp/www aaron@X.X.29.13's password:
  正常情况下输入aaron用户的密码即可完成复制！！但此次复制没有成功出现如下提示：
  scp: /tmp/www/xinpindao: Permission denied 排错： 重新查看scp命令。。。没有问题！！ 
  重新输入口令。。。没有错误！！
  查看远程机目录权限。。。 drwxr-xr-x 2 root  root  4096 May  7 17:30 www
  原来问题出现在这儿，此目录是后来使用root用户创建，但是对于aaron用来来讲，没有写入权限，
  更改权限 %chmod -R  777   /tmp/www 再次执行上述命令。。。成功！！！
  总结：当使用scp命令进行文件复制时如果出现文件权限问题，请仔细检查目录权限，小的细节请引起注意！
  ！ 实践二例： %scp   /www/xinpindao    root@X.X.29.18:/tmp   
  远程机用户root root@X.X.29.18's password:  Permission denied, please try again.
  经过多次检查后最终发现-为保证安全前期布署过程中已将ssh服务关闭root用户的登录权限 解决方法：
  要修改root的ssh权限，即修改 /etc/ssh/sshd_config文件中
   PermitRootLogin no 改为 PermitRootLogin yes
   重启ssh服务  %/etc/init.d/sshd   restart   重新测试成功！！！
 ----------------------------------------------------------------------
$ mysql -u root -p < schema.sql
服务器端准备就绪。

部署

用FTP还是SCP还是rsync复制文件？如果你需要手动复制，用一次两次还行，一天如果部署50次不但慢、效率低，
而且容易出错。

正确的部署方式是使用工具配合脚本完成自动化部署。Fabric就是一个自动化部署工具。
由于Fabric是用Python 2.x开发的，所以，部署脚本要用Python 2.7来编写，本机还必须安装Python 2.7版本。

要用Fabric部署，需要在本机（是开发机器，不是Linux服务器）安装Fabric：

$ easy_install fabric
pip uninstall paramiko
pip install paramiko==1.14.0
Linux服务器上不需要安装Fabric，Fabric使用SSH直接登录服务器并执行部署命令。

下一步是编写部署脚本。Fabric的部署脚本叫fabfile.py，我们把它放到awesome-python-webapp的目录下，
与www目录平级：

awesome-python-webapp/
+- fabfile.py
+- www/
+- ...
Fabric的脚本编写很简单，首先导入Fabric的API，设置部署时的变量：
然后，每个Python函数都是一个任务。我们先编写一个打包的任务：

Fabric提供local('...')来运行本地命令，with lcd(path)可以把当前命令的目录设定为lcd()指定的目录，
注意Fabric只能运行命令行命令，Windows下可能需要Cgywin环境。

在awesome-python-webapp目录下运行：

$ fab build
看看是否在dist目录下创建了dist-awesome.tar.gz的文件。

打包后，我们就可以继续编写deploy任务，把打包文件上传至服务器，解压，重置www软链接，重启相关服务：

注意run()函数执行的命令是在服务器上运行，with cd(path)和with lcd(path)类似，
把当前目录在服务器端设置为cd()指定的目录。如果一个命令需要sudo权限，就不能用run()，而是用sudo()来执行。

配置Supervisor

上面让Supervisor重启awesome的命令会失败，因为我们还没有配置Supervisor呢。

编写一个Supervisor的配置文件awesome.conf，存放到/etc/supervisor/conf.d/目录下：

配置文件通过[program:awesome]指定服务名为awesome，command指定启动app.py。

然后重启Supervisor后，就可以随时启动和停止Supervisor管理的服务了：
$ sudo supervisorctl reload
$ sudo supervisorctl start awesome
$ sudo supervisorctl status
awesome                RUNNING    pid 1401, uptime 5:01:34

配置Nginx

Supervisor只负责运行gunicorn，我们还需要配置Nginx。把配置文件awesome放到/etc/nginx/sites-available/目录下：


然后在/etc/nginx/sites-enabled/目录下创建软链接：

$ pwd
/etc/nginx/sites-enabled
$ sudo ln -s /etc/nginx/sites-available/awesome .
让Nginx重新加载配置文件，不出意外，我们的awesome-python3-webapp应该正常运行：

$ sudo /etc/init.d/nginx reload
如果有任何错误，都可以在/srv/awesome/log下查找Nginx和App本身的log。如果Supervisor启动时报错，
可以在/var/log/supervisor下查看Supervisor的log。

如果一切顺利，你可以在浏览器中访问Linux服务器上的awesome-python3-webapp了：

如果在开发环境更新了代码，只需要在命令行执行：

$ fab build
$ fab deploy
自动部署完成！刷新浏览器就可以看到服务器代码更新后的效果。


头像上传实际上是文件上传，文件上传不是普通的application/x-www-form-urlencoded，
而是mutipart/form-data，需要middleware解析multipart才行。

不过html5已经能读取用户选择的本地文件了，可以用javascript把文件内容读出来，
用base64编码后当作字符串通过ajax发送到服务器，就是一个普通的x-www-form-urlencoded，服务器拿到字符串，base64解码，获得图片本身。
注意: linux下的换行时\n,而windows下是\r\n;在移植到linux时,要将py文件中的所有\r\n替换为\n;否则,linux将不能执行py;因为读取第一行时,会失败
'''
