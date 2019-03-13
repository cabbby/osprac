# 操统实习 第二次报告

### **rootfs 制作流程**


### **fakeContainer - CPU 压力测试**

在 fakeContainer.c 中，通过 cgroup 将可用 CPU 限制为了 CPU0

#### 测试 1
```
stress -c 2
```

这一命令调用 stress 创建了两个不断执行 sqrt 的进程，测试结果如下：

![avatar](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_cpu_2.png)

可以看到，使用 cgroup 后，进程仅能执行在 CPU0 上。

如果不用 cgroup 限制可用的 CPU，则两个 CPU 会同时执行进程。


### **fakeContainer - 内存压力测试**

在 fakeContainer.c 中，通过 cgroup 限制最大可用内存为 512M

#### 测试 1
```
stress --vm 1 --vm-bytes 510M --vm-keep
```

创建了一个申请 510M 内存并不断对其读写的进程，测试结果如下：

![avatar](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_mem_510M.png)

#### 测试 2
```
stress --vm 1 --vm-bytes 1024M --vm-keep
```

创建了一个申请 1024M 内存并不断对其读写的进程，测试结果如下：

![avatar](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_mem_1024M.png)

#### 测试 3
```
stress --vm 1 --vm-bytes 1536M --vm-keep
```

创建了一个申请 1536M 内存并不断对其读写的进程，测试结果如下：

![avatar](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_mem_1536M.png)

#### 测试 4
```
stress --vm 1 --vm-bytes 2048M --vm-keep
```

创建了一个申请 1024M 内存并不断对其读写的进程，测试结果如下：

![avatar](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_mem_2048M.png)

#### 测试 5
```
stress --vm 1 --vm-bytes 512M --vm-keep
```

创建了一个申请 512M 内存并不断对其读写的进程，测试结果如下：

![avatar](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_mem_512M.png)

#### 容器内进程内存占用超出 cgroup 限制后的行为

一个进程可以申请一定量的虚拟内存：
* 在虚拟内存量不超过 cgroup 的物理内存限制时，虚拟内存会直接映射到物理内存
* 当虚拟内存量超出限制时，进程并不会出错。超过的部分将会通过 swap 机制利用磁盘空间进行交换
* 当虚拟内存量超出 (物理内存限制 + swap 大小) 时，进程会被 OOM Killer 杀死
