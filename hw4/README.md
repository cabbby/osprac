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

称 162.105.175.60 为 vm1, 162.105.175.61 为 vm2

在 vm1 上为两个用户分别创建两个容器：

```
lxc-create -n usr1-1 -t ubuntu
lxc-create -n usr2-1 -t ubuntu
```

在 vm2 上为两个用户分别创建两个容器：

```
lxc-create -n usr1-2 -t ubuntu
lxc-create -n usr2-2 -t ubuntu
```

在 vm1 上：

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

```
# 设置 host 上网桥和与容器 usr1-1, usr2-1 连接的veth pair
ovs-vsctl add-br vm1-br
ovs-vsctl add-port vm1-br usr1-1-veth
ovs-vsctl set port usr1-1-veth tag=101
ovs-vsctl add-port vm1-br usr2-1-veth
ovs-vsctl set port usr2-1-veth tag=102

设置网关
ovs-vsctl add-port vm1-br usr1-gw tag=101 -- set interface usr1-gw type=internal
ip address add 192.168.1.1/16 dev usr1-gw
ip link set usr1-gw up
ovs-vsctl add-port vm1-br usr2-gw tag=102 -- set interface usr2-gw type=internal
ip address add 192.168.2.1/16 dev usr2-gw
ip link set usr2-gw up

iptables -t nat -A POSTROUTING -s 192.168.88.0/24 -j MASQUERADE
```

在每个容器中：
```
echo "nameserver 162.105.129.26" >> /etc/resolv.conf
```