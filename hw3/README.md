# 操统实习 第三次报告

## Linux 网络包处理过程

网络包到达时，先经过 PREROUTING 链。如果目的地为本机，则进入 INPUT 链，否则进入 FORWARD 链。进入 INPUT 链的包被本机进程处理后，发出的包进入 OUTPUT 链。包经过 FORWARD 链和 OUTPUT 链后再进入 POSTROUTING 链，最后发出。

* PREROUTING 链包含表 raw, mangle, nat
* FORWARD 链包含 mangle, filter 表
* POSTROUTING 链包含 mangle, nat 表
* INPUT 链包含 mangle, nat 表
* OUTPUT 链包含 raw, mangle, nat, filter 表

<br>

## iptables 测试

### 拒绝来自某一特定 IP 地址的访问

在 162.105.175.60 上 ping 162.105.175.61:

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/m1_1.png)

在 162.105.175.61 上添加规则：
```
iptables -A INPUT -s 162.105.175.60 -j DROP
```

在 INPUT 链上丢弃所有来自 162.105.175.60 的包：

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/m2_1.png)

再观察 ping 的输出：

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/m1_2.png)

可以发现 ping 没有新的显示，说明 iptables 起效。

在 162.105.175.61 上删除规则：iptables -D INPUT 5

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/m2_2.png)

再观察 162.105.175.60 上的 ping 输出：

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/m1_3.png)

可以发现 ping 继续工作，说明规则删除成功。观察 icmp_seq 的变化可以得知中间的数据包即为被丢弃的包。

通过另外测试可以验证，规则生效时主机的 ssh 等服务同样不能访问。

### 只开放 http 服务和 ssh 服务，其余拒绝

在 162.105.175.51 上修改规则：
```
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A OUTPUT -p tcp --sport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A OUTPUT -p tcp --sport 22 -j ACCEPT
iptables -P INPUT DROP
iptables -P OUTPUT DROP
```

注意要在修改 INPUT 和 OUTPUT 的默认策略为 DROP 前，一定要设定 ssh 端口为 ACCEPT，否则会无法连接。

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/t2_1.png)

查看现有规则：

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/t2_2.png)

经测试，只能通过 ssh(22) 端口和 http(80) 端口访问机器。

### 拒绝回应来自某特定 IP 的 ping 命令

在 162.106.175.60 上添加规则：
```
iptables -A OUTPUT -d 162.105.175.60 -p icmp --icmp-type echo-reply -j DROP
```

可以验证，执行命令后，162.105.175.60 无法 ping 通本机。

<br>

## "路由" 和 "交换" 的区别

* 路由在网络层，路由器根据 IP 地址寻址；交换机在数据链路层，根据 MAC 地址寻址。路由器可以处理 TCP/IP 协议，交换机不可以。

* 路由器将一个 IP 分配给多台机器使用，对外只表现为一个 IP；交换机将多个主机连接起来，每台主机对外有不同的 IP。

* 路由器可以提供防火墙功能；交换机不可以。

<br>

## fakeContainer 网络实现

TODO