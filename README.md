- 第一次使用create_table创建记录账号信息表单
- 调用insertdb插入账号
- 推荐使用supervisor部署后台托管，screen也可，但是易被杀进程


supervisor配置：
```
[program:BilibiliTool]
command=python -u /root/BilibiliTool/bilibiliexp.py
autostart=true
autorestart=true
directory=/root/BilibiliTool
stdout_logfile=/var/log/BilibiliTool.log
redirect_stderr=true
```
