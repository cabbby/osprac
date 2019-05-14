# 操统实习 第五次报告

## Raft 算法

Raft 是一个用于解决分布式系统中一致性问题的算法。

Raft 算法将节点分为 3 类角色：

1. Leader：接收 Client 的请求，将日志复制到其它节点

2. Candidate：Leader 的候选人

3. Follower：响应 Leader 和 Candidate 的请求

Leader 选举遵循以下规则：

1. 初始时所有节点都是 Follower。一个 Follower 在一个 Term 中只有一次投票机会。

2. 每个 Follower 有一个随机的超时时限，如果在时限内未接收到来自 Leader 的 Heartbeat 信息或 Candidate 的 RequestVote 信息，则自己成为 Candidate。

3. 节点成为 Candidate 时，向其它节点发出 RequestVote 信息，请求投票。

4. 一个 Candidate 得到集群中超过半数节点的投票，则成为 Leader。Term 增加 1。

5. Leader 定时向其它节点发出 Heartbeat 信息维持统治。

日志复制遵循以下原则：

Leader 接收来自 Client 的请求，将其写入日志，通过下次 Heartbeat 信息告知其它节点。得到其它节点的确认信息后，Leader 应用这一请求，通过 Heartbeat 告知其它节点应用请求。

<br>

场景模拟：

共 4 个节点，最初所有节点都是 Follower。

节点 1、2 同时到达超时时限，向其它节点发出 RequestVote 信息。

节点 3 回应节点 1 的请求，节点 4 回应节点 2 的请求。

节点 1、2 都未得到超过半数票，进入下一个选举周期。

节点 3 最先到达时限，向其它节点发出 RequestVote 信息。

节点 1、2、4 回应节点 3 的请求，节点 3 成为 Leader。



## GlusterFS & AUFS

GlusterFS 是一个无元数据服务器的分布式文件系统，具有以下技术特点：

1. 完全在软件层面上实现，无需特殊硬件支持。

2. 在用户空间实现，无需干涉内核，降低了用户自定义成本。

3. 采用模块化、堆栈式的架构，灵活、模块化、高度可定制。

4. 无元数据服务器的设计避免了单点故障和性能瓶颈问题。


AUFS 是一种联合文件系统，支持将不同物理位置的文件夹合并为一个文件夹，并且可以分别设置读写权限。Docker 就使用 AUFS 作为其镜像分层技术的实现基础。使用 AUFS，可以减少不同容器镜像之间重复内容的冗余。


## GlusterFS 配置

称 gfs01 为 162.105.175.60，gfs02 为 162.105.175.61

往两台机器以及 gfs02 上的容器 lxc2 的 hosts 追加：

```
162.105.175.60 gfs01
162.105.175.61 gfs02
```

安装并启动 glusterfs：

``` bash
sudo apt install glusterfs-server

sudo systemctl start glusterfs-server
sudo systemctl enable glusterfs-server
```

在 gfs01 上：

``` bash
sudo gluster peer probe gfs02
```

在两台机器上：

``` bash
sudo mkdir -p /glusterfs/distributed
```

在 gfs01 上：

``` bash
# 创建 replicated volume
sudo gluster volume create v01 replica 2 transport tcp gfs01:/glusterfs/distributed gfs02:/glusterfs/distributed force
```

在容器中：

``` bash
# 创建 /dev/fuse （LXC 容器中需手动添加）
sudo mknod /dev/fuse c 10 229 

# 安装并配置 glusterfs client
sudo apt install glusterfs-client
sudo mkdir -p /mnt/glusterfs
sudo mount -t glusterfs gfs01:/v01 /mnt/glusterfs/
```

搭建完毕。进行测试：

在容器中运行：

``` bash
touch /mnt/glusterfs/a
touch /mnt/glusterfs/b
```

可以在 gfs01, gfs02 的 /glusterfs/distributed 文件夹中观察到文件的同步。

将 gfs01 关机，再在容器中运行：

``` bash
touch /mnt/glusterfs/c
```

发现操作可正常执行，并且在 gfs02 的 /glusterfs/distributed 文件夹中观察到文件的同步。重启 gfs01 后，文件同样会同步。说明了该文件系统的容错性。

## AUFS 配置 LXC 镜像

以下命令均在 root 下执行：

``` bash
# 创建两个容器
lxc-create -n cont1 -t ubuntu
lxc-create -n cont2 -t ubuntu

# 获得基本镜像，并删除两个容器原有 rootfs
cd /var/lib/lxc
mv ./cont1/rootfs ./base-rootfs
rm -rf ./cont2/rootfs

# 创建 rootfs 挂载点和用于存储更改的镜像的挂载点
mkdir ./cont1/rootfs ./cont1/storage
mkdir ./cont2/rootfs ./cont2/storage

# 将基本镜像以只读方式和用于存储更改的镜像以 AUFS 方式挂载到容器的 rootfs
mount -t aufs -o dirs=./cont1/storage:./base-rootfs none ./cont1/rootfs
mount -t aufs -o dirs=./cont2/storage:./base-rootfs none ./cont2/rootfs
```

配置完毕。在两个容器中作出不同更改，可以发现共享的基本镜像不会改变，改变只反映在各自的存储镜像上。