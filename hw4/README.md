# 操统实习 第四次报告

## 网络处理过程分析

1. 同一 host 上同一子网内的两容器<br>
host 上有网桥 bridge，两对 veth pair 将两个容器连接到 bridge 上。容器间通信时，一个容器发出的数据包通过 veth pair 到达 bridge，然后通过另一个容器与 bridge 间的 veth pair 到达目标容器。

2. 同一 host 上不同子网内的两容器<br>
源容器发出数据包，通过 veth pair 到达 host 上的网桥，但由于 VLAN 不同的限制，并不能直接到达 host 上的目标容器，而是先到源容器所属子网的网关接口，然后到目标容器所属子网的网关接口，再送回网桥，通过 veth pair 最终到达目标容器。

3. 通过 GRE 隧道相连的两个 host 上同一子网内的两容器<br>
源容器发出数据包，通过 veth pair 到达 host 上的网桥，然后通过 GRE 隧道到达网关所在 host 的网桥，再通过 GRE 隧道到目标容器所在 host 的网桥，最后通过 veth pair 到达目标容器。

## VLAN

VLAN 是将一个物理局域网划分为多个逻辑上的虚拟局域网，从而达到划分广播域的技术。使用 IEEE802.1Q 时，在数据帧中附加 VLAN 识别信息，并在交换机端口上设置允许通过的 VLAN ID，达到实现 VLAN 的目的。

IEEE802.1Q 是对数据帧附加 VLAN 识别信息的协议。一个数据帧中有 4 byte 作为 VLAN 识别信息，包含 2 byte 的 TPID 和 2 byte 的 TCI。其中 TPID 固定为 0x8100，交换机通过 TPID 确定数据帧中附加了基于 IEEE802.1Q 的 VLAN 识别信息。TCI 中有 12 bit 作为实质上的 VLAN ID，故总共最多能识别 4096 个 VLAN。

## VXLAN 与 GRE

VXLAN 是一种覆盖网络技术或隧道技术，是对 VLAN 的扩展。VXLAN 将虚拟机发出的数据包封装在 UDP 中，并使用物理网络的 IP/MAC 作为 outer-header 进行封装，然后在物理 IP 网上传输，到达目的地后由隧道终结点解封并将数据发送给目标虚拟机。本质是对数据链路层的数据帧头重新定义再通过传输层的 UDP 连接进行传输。由于在隧道两端直接建立连接，因此如果需要在中途截获数据包并对其进行一些解析操作（如流量统计），则需要在中途设置物理设备作为 VXLAN 网关，开销较大。

GRE 本质是在隧道的两端的传输层建立 UDP 连接传输重新包装的网络层包头，到目的地再取出包装后的包头进行解析。GRE 本质上是点对点的，在大规模网络中，隧道数量将会无法承受。


## LXC 容器集群构建

### 目标

采用多网桥无 VLAN 方式实现容器集群。

称 162.105.175.60 为 vm1, 162.105.175.61 为 vm2。

* 在 vm1 上创建两个容器 usr1-1(192.168.1.2), usr2-1(192.168.2.2)，在 vm2 上创建两个容器 usr1-2(192.168.1.3), usr2-2(192.168.2.3)
* usr1-1 和 usr1-2 属于用户 1，usr2-1 和 usr2-2 属于用户 2
* 用户 1 和用户 2 的容器分属不连通的内网，同时容器都能访问外网。用户 1 的网关为 192.168.1.1，用户 2 的网关为 192.168.2.1。网关设置在 vm1 上

### 步骤

在 vm1 上：

创建容器 usr1-1, usr2-1：

```
lxc-create -n usr1-1 -t ubuntu
lxc-create -n usr2-1 -t ubuntu
```

修改 /var/lib/lxc/usr1-1/config:
```
# Common configuration
lxc.include = /usr/share/lxc/config/ubuntu.common.conf

# Container specific configuration
lxc.rootfs = /var/lib/lxc/usr1-1/rootfs
lxc.rootfs.backend = dir
lxc.utsname = usr1-1
lxc.arch = amd64

# Network configuration
lxc.network.type = veth
# lxc.network.link = lxcbr0
lxc.network.name = eth0
lxc.network.veth.pair = usr1-1-veth
lxc.network.ipv4 = 192.168.1.2/24
lxc.network.ipv4.gateway = 192.168.1.1
lxc.network.flags = up
lxc.network.hwaddr = 00:16:3e:0c:07:73
```

修改 /var/lib/lxc/usr2-1/config:
```
# Common configuration
lxc.include = /usr/share/lxc/config/ubuntu.common.conf

# Container specific configuration
lxc.rootfs = /var/lib/lxc/usr2-1/rootfs
lxc.rootfs.backend = dir
lxc.utsname = usr2-1
lxc.arch = amd64

# Network configuration
lxc.network.type = veth
#lxc.network.link = lxcbr0
lxc.network.name = eth0
lxc.network.veth.pair = usr2-1-veth
lxc.network.ipv4 = 192.168.2.2/24
lxc.network.ipv4.gateway = 192.168.2.1
lxc.network.flags = up
lxc.network.hwaddr = 00:16:3e:a3:ba:15
```

执行命令：

```
# 为用户分别配置网桥和网关，将容器 usr1-1, usr2-1 连接到网桥上
ovs-vsctl add-br br-usr1
ovs-vsctl add-port br-usr1 usr1-1-veth
ovs-vsctl add-port br-usr1 gw-usr1 -- set interface gw-usr1 type=internal
ip address add 192.168.1.1/24 dev gw-usr1
ip link set gw-usr1 up

ovs-vsctl add-br br-usr2
ovs-vsctl add-port br-usr2 usr2-1-veth
ovs-vsctl add-port br-usr2 gw-usr2 -- set interface gw-usr2 type=internal
ip address add 192.168.2.1/24 dev gw-usr2
ip link set gw-usr2 up

# 配置 GRE 隧道
ovs-vsctl add-port br-usr1 gre-usr1-vm1
ovs-vsctl set interface gre-usr1-vm1 type=gre options:remote_ip=162.105.175.61 options:key=1
ovs-vsctl add-port br-usr2 gre-usr2-vm1
ovs-vsctl set interface gre-usr2-vm1 type=gre options:remote_ip=162.105.175.61 options:key=2

# 设置 iptables 规则
iptables -A INPUT -s 192.168.1.0/24 -d 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -s 192.168.2.0/24 -d 192.168.2.0/24 -j ACCEPT
iptables -A INPUT -s 192.168.0.0/16 -d 192.168.0.0/16 -j REJECT
iptables -A FORWARD -s 192.168.0.0/16 -d 192.168.0.0/16 -j REJECT
iptables -t nat -A POSTROUTING -s 192.168.0.0/16 -j MASQUERADE
```

---

在 vm2 上：

创建容器 usr1-2, usr2-2:

```
lxc-create -n usr1-2 -t ubuntu
lxc-create -n usr2-2 -t ubuntu
```

修改 /var/lib/lxc/usr1-2/config:
```
# Common configuration
lxc.include = /usr/share/lxc/config/ubuntu.common.conf

# Container specific configuration
lxc.rootfs = /var/lib/lxc/usr1-2/rootfs
lxc.rootfs.backend = dir
lxc.utsname = usr1-2
lxc.arch = amd64

# Network configuration
lxc.network.type = veth
# lxc.network.link = lxcbr0
lxc.network.name = eth0
lxc.network.veth.pair = usr1-2-veth
lxc.network.ipv4 = 192.168.1.3/24
lxc.network.ipv4.gateway = 192.168.1.1
lxc.network.flags = up
lxc.network.hwaddr = 00:16:3e:29:de:c9
```

修改 /var/lib/lxc/usr2-2/config:
```
# Common configuration
lxc.include = /usr/share/lxc/config/ubuntu.common.conf

# Container specific configuration
lxc.rootfs = /var/lib/lxc/usr2-2/rootfs
lxc.rootfs.backend = dir
lxc.utsname = usr2-2
lxc.arch = amd64

# Network configuration
lxc.network.type = veth
# lxc.network.link = lxcbr0
lxc.network.name = eth0
lxc.network.veth.pair = usr2-2-veth
lxc.network.ipv4 = 192.168.2.3/24
lxc.network.ipv4.gateway = 192.168.2.1
lxc.network.flags = up
lxc.network.hwaddr = 00:16:3e:1e:d5:3f
```

执行命令：

```
# 为用户分别配置网桥，将容器 usr1-2, usr2-2 连接到网桥上
ovs-vsctl add-br br-usr1
ovs-vsctl add-port br-usr1 usr1-2-veth

ovs-vsctl add-br br-usr2
ovs-vsctl add-port br-usr2 usr2-2-veth

# 配置 GRE 隧道
ovs-vsctl add-port br-usr1 gre-usr1-vm2
ovs-vsctl set interface gre-usr1-vm2 type=gre options:remote_ip=162.105.175.60 options:key=1
ovs-vsctl add-port br-usr2 gre-usr2-vm2
ovs-vsctl set interface gre-usr2-vm2 type=gre options:remote_ip=162.105.175.60 options:key=2
```

在每个容器中配置 DNS：
```
echo "nameserver 162.105.129.26" >> /etc/resolv.conf
```

### 测试

经过上面的步骤，所有容器都能访问外网，usr1-1, usr1-2 可以互相 ping 通，usr2-1, usr2-2 可以互相 ping 通，且两不同子网间容器互相 ping 不通，说明达到效果。

在 vm1 上通过 netperf 测试带宽：

```
# 在 usr1-1 上测试访问 vm2 时的带宽
root@usr1-1:/# netperf -H 162.105.175.61
MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 162.105.175.61 () port 0 AF_INET : demo
Recv   Send    Send                          
Socket Socket  Message  Elapsed              
Size   Size    Size     Time     Throughput  
bytes  bytes   bytes    secs.    10^6bits/sec  

 87380  16384  16384    10.14     239.21

# 在 usr2-1 上测试访问 vm2 时的带宽
root@usr2-1:/# netperf -H 162.105.175.61
MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 162.105.175.61 () port 0 AF_INET : demo
Recv   Send    Send                          
Socket Socket  Message  Elapsed              
Size   Size    Size     Time     Throughput  
bytes  bytes   bytes    secs.    10^6bits/sec  

 87380  16384  16384    10.13     243.57
```

可以看到，默认情况下，网关大约允许 240 Mbps 的吞吐量。

现在 vm1 上执行命令，对网关进行限速：

```
# 将用户 1 的网关的带宽限制为 1 Mbps
ovs-vsctl set interface gw-usr1 ingress_policing_rate=1000
ovs-vsctl set interface gw-usr1 ingress_policing_burst=100

# 将用户 2 的网关的带宽限制为 10 Mbps
ovs-vsctl set interface gw-usr2 ingress_policing_rate=10000
ovs-vsctl set interface gw-usr2 ingress_policing_burst=1000
```

测试带宽：
```
root@usr1-1:/# netperf -H 162.105.175.61
MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 162.105.175.61 () port 0 AF_INET : demo
Recv   Send    Send                          
Socket Socket  Message  Elapsed              
Size   Size    Size     Time     Throughput  
bytes  bytes   bytes    secs.    10^6bits/sec  

 87380  16384  16384    10.90       0.47

root@usr2-1:/# netperf -H 162.105.175.61
MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 162.105.175.61 () port 0 AF_INET : demo
Recv   Send    Send                          
Socket Socket  Message  Elapsed              
Size   Size    Size     Time     Throughput  
bytes  bytes   bytes    secs.    10^6bits/sec  

 87380  16384  16384    10.50       5.07
```

可以发现，流量限制起到了作用。带宽减半是因为同一网关上两个容器的平均分配。