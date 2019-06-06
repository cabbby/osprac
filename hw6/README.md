# 操统实习 期末Project报告：面向单用户的作业管理系统

## 效果展示

Web界面

![](https://github.com/cabbby/osprac/blob/master/hw6/pics/ui1.png)

![](https://github.com/cabbby/osprac/blob/master/hw6/pics/ui2.png)

任务详情页面

![](https://github.com/cabbby/osprac/blob/master/hw6/pics/details.png)

## 整体架构

![](https://github.com/cabbby/osprac/blob/master/hw6/pics/structure.png)

### 任务

称提交到Master上的任务为Job，分配到Node的任务为Task

每个任务有jobId, taskId

任务状态：

* Pending[ ]：任务暂未被分配到Node上
* Pending[A]：任务已被分配到某一Node上，但还未开始执行
* Running：任务正在运行
* Finished：任务正常结束
* Timeout：任务超市
* Failed：任务异常结束
* Killed：任务被强制终止

### 存储

在Master和Node上分别调用config-glusterfs-master, config-glusterfs-master脚本来进行存储配置

通过Glusterfs建立了共享目录，用于存储共享数据，在Master和各个Node上将其挂载为/mnt/share

/mnt/share/nodes/[nodeId]/task[taskId]目录下保存有任务相关输出：
* monitor_out：TaskMonitor的日志输出
* task_stdout：任务标准输出流
* task_stderr：任务标准错误流

## 代码结构

采用Python和Bash脚本语言编写

- Master
    * master/config-glusterfs-master：在Master上初始化存储所用脚本
    * master/MasterServer.py：Master的Web服务实现
    * master/MasterMonitor.py：Master后台逻辑的实现
    * master/MasterProfile.py：保存Master的一些配置
    * master/JobTable.py：将任务列表解析为HTML表格的辅助类
    * master/NodeTable.py：将Node列表解析为HTML表格的辅助类
    * master/templates/：包含渲染Web界面所用HTML模板

- Node
    * node/config-glusterfs-node：在Node上初始化存储所用脚本
    * node/create-container：在Node上创建并配置一个容器所用脚本
    * node/delete-container：在Node上删除一个容器所用脚本
    * node/NodeServer.py：Node的Web服务实现
    * node/NodeMonitor.py：Node后台逻辑的实现
    * node/NodeProfile.py：保存Node的一些配置
    * node/TaskMonitor.py：用作任务守护进程

## Master

分为两个线程：HTTP服务器线程，数据更新线程

HTTP服务器线程响应来自用户的HTTP请求，支持 HTTP API:

* /job/create：创建单个任务
* /job/create_json：根据json创建多个任务
* /job/kill：终止任务
* /job/details：获取任务详情

初始化时，Master从MasterProfile中读取Node的配置情况

调用/job/create后，Master更新内部的Job列表

在数据更新线程中，每隔一定interval，通过与各Node通信，更新任务状态

若有任务需要被调度，则尝试将其调配给当前空闲内存最多的Node


## Node

分为两个线程：HTTP服务器线程，数据更新线程

HTTP服务器线程响应来自用户的HTTP请求，支持 HTTP API:

* /resource：查询剩余资源
* /task/create：创建任务
* /task/kill：终止任务
* /task/info：获取任务详情

初始化时，从NodeProfile中读取nodeId、资源总量

调用/task/create后，Node更新内部的Task列表，通过subprocess启动守护进程TaskMonitor

在数据更新线程中，每隔一定interval，从/mnt/share/nodes/[nodeId]/task[taskId]/monitor_out中读取日志信息，更新Task状态


## TaskMonitor

调用create-container脚本创建、配置容器

在子进程中执行命令，启动重定向stdout, stderr

在主线程中检查超时情况

任务Timeout/接受来自Node的SIGTERM信号（即收到Kill请求）时强制结束进程

进程终止后，调用delete-containter脚本删除容器


## create-container

### 容器镜像管理

每台Node机器上/root/img目录下存储所有镜像

/root/cont/[contId]/usrfile作为可写层

/root/cont/[contId]/usrfile/workspace为用户命令的执行目录

使用AUFS将基本镜像和用户文件挂载为容器的rootfs

### cgroup配置

直接写入LXC配置文件