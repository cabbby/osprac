# 操统实习 第二次报告

### **rootfs 制作流程**

### **fakeContainer - CPU 压力测试**

![avatar](https://github.com/cabbby/osprac/blob/master/hw2/pics/test_cpu_2.png)

关于容器内进程内存占用超出 cgroup 限制后的行为：

一个进程可以申请一定量的虚拟内存：
* 在虚拟内存量不超过 cgroup 的物理内存限制时，虚拟内存会直接映射到物理内存
* 当虚拟内存量超出限制时，进程并不会出错。超过的部分将会通过 swap 机制利用磁盘空间进行交换
* 当虚拟内存量超出 (物理内存限制 + swap 大小) 时，进程会被 OOM Killer 杀死
