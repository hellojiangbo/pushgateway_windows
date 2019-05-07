具体功能: 
将node_exporter、curl、ping丢包率等信息推送给pushgateway; 
1. 收集客户端网卡信息.
2. 获取客户端公网IP
3. 获取ping延时和丢包率
4. 推送wmi_exporter 9182端口信息到pushgateway
5. 获取打开网站的速度

前提必须安装python3、node_exporter
1. node_exporter、curl、ping、pushgateway域名和端口可以自定义，请参考getinfo.cfg 。
2. pushgateway 用户名和密码，可通过nginx进行认证
3. 编译成exe程序命令: pyinstaller -F -w pushgateway_windows.py

无法运行的可能原因
1. getinfo.google.cn 域名不通
2. 没有配置文件: getinfo.cfg
