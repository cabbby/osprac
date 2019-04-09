# 操统实习 第三次报告

## iptables 测试

在 162.105.175.60 上 ping 162.105.175.61:

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/m1_1.png)

在 162.105.175.61 上添加规则：iptables -A INPUT -s 162.105.175.60 -j DROP

在 INPUT 链上丢弃所有来自 162.105.175.60 的包：

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/m1_2.png)

可以发现 ping 没有新的显示，说明 iptables 起效。

在 162.105.175.61 上删除规则：iptables -D INPUT 5

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/m2_2.png)

再观察 162.105.175.60 上的 ping 输出：

![](https://github.com/cabbby/osprac/blob/master/hw3/pics/m1_3.png)

可以发现 ping 继续工作，说明规则删除成功。




## CPU 压力测试

在 fakeContainer.c 中，通过 cgroup 将可用 CPU 限制为 CPU0

### 测试 1
```
stress -c 2
```

这一命令调用 stress 创建了两个不断执行 sqrt 的进程，测试结果如下：

![](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_cpu_2.png)

可以看到，使用 cgroup 后，进程仅能执行在 CPU0 上。

如果不用 cgroup 限制可用的 CPU，则两个 CPU 会同时执行进程。


## 内存压力测试

在 fakeContainer.c 中，通过 cgroup 限制最大可用内存为 512M

### 测试 1
```
stress --vm 1 --vm-bytes 510M --vm-keep
```

创建了一个申请 510M 内存并不断对其读写的进程，测试结果如下：

![](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_mem_510M.png)

VIRT, RES, SWAP 列分别为 虚拟内存总占用量、实际物理内存占用量，交换空间占用量。USED = RES + SWAP。

结果与参数基本吻合。

### 测试 2
```
stress --vm 1 --vm-bytes 1024M --vm-keep
```

创建了一个申请 1024M 内存并不断对其读写的进程，测试结果如下：

![](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_mem_1024M.png)

进程的物理内存量受 cgroup 限制，基本和参数符合。同时超出部分使用 swap 进行交换。两者都近似 512M。

总和 USED 为 1G。

### 测试 3
```
stress --vm 1 --vm-bytes 1536M --vm-keep
```

创建了一个申请 1536M 内存并不断对其读写的进程，测试结果如下：

![](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_mem_1536M.png)

此时物理内存用量受限制，为 512M。超出部分 1G 使用 swap。

### 测试 4
```
stress --vm 1 --vm-bytes 2048M --vm-keep
```

创建了一个申请 2048M 内存并不断对其读写的进程，测试结果如下：

![](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_mem_2048M.png)

可以发现，进程申请的内存空间超过物理内存限制和 swap 总和后，程序被强行终止。

### 测试 5
```
stress --vm 1 --vm-bytes 512M --vm-keep
```

创建了一个申请 512M 内存并不断对其读写的进程，测试结果如下：

![](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_mem_512M.png)

可以发现，由于申请内存和 cgroup 限制近似相等，进程本身基本没有占用 swap。

但在这种情况下，系统本身（或其它因素造成）的 swap 开销处于周期性的波动状态。

经过多次试验可以发现，申请空间达到 512M 这一限制后突然开始出现这种波动，且随着申请空间变大，波动逐渐变缓。

原因尚需进一步了解。

### 容器内进程内存占用超出 cgroup 限制后的行为

一个进程可以申请一定量的虚拟内存：
* 在虚拟内存量不超过 cgroup 的物理内存限制时，虚拟内存会直接映射到物理内存
* 当虚拟内存量超出限制时，进程并不会出错。超过的部分将会通过 swap 机制利用磁盘空间进行交换
* 当虚拟内存量超出 (物理内存限制 + swap 大小) 时，进程会被 OOM Killer 杀死


## 改进设想

* 初始进程 <br>
考虑停止容器时的情况。<br>
fakeContainer 的初始进程为 bash，它接受 SIGTERM 信号时并不会将 SIGTERM 转发到子进程。如果在 host 上通过 kill 向容器初始进程发送一个 SIGTERM，会导致容器中所有进程被杀死，但是容器初始进程并未回收它的子进程。这会导致 zombie process 的产生。<br>
很自然的想法是在 bash 结束时向所有子进程发送信号。但 bash 是可能在它的子进程全部终止之前就结束的。因此还需要等待所有子进程结束才能终止。<br>
因此我们需要一个自定义一个更完善的容器初始进程来解决这些问题。同时，还可以利用它来实现一些容器内日志记录等功能。

* 资源隔离 <br>
fakeContainer 的资源隔离功能还很有限，例如无法控制 CPU使用率、 swap 的使用、IO 吞吐量等等。

* 网络 <br>
容器显然需要某种方式，来与主机或其他容器进行通信。由于它们在逻辑上都是互相隔离的机器，因此网络便是一个很好的途径。同时，很多应用场景本身也需要与网络上其他机器进行通信。故，让容器支持网络是一个很重要的待改进处。
