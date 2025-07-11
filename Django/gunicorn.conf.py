# Gunicorn配置文件
import multiprocessing

# 绑定的IP和端口
bind = "127.0.0.1:8000"

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "sync"

# 最大请求数
max_requests = 1000
max_requests_jitter = 50

# 超时时间
timeout = 30
keepalive = 2

# 日志配置
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# 进程名称
proc_name = "program-04"

# 用户和组（需要创建）
# user = "www-data"
# group = "www-data"

# 预加载应用
preload_app = True

# 守护进程
daemon = False 