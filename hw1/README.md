# 操统实习 第一次报告：虚拟机技术和容器技术

## Virtual Machine (Hardware virtualization)
在硬件层次上对宿主机进行抽象和隔离。

核心：Hypervisor(or VMM, Virtual Machine Monitor)

它是介于虚拟机与宿主机的一层中间软件，负责管理虚拟机、协调它们对硬件资源的访问。

Hypervisor分为native和hosted两种：

* native hypervisor：
直接运行在硬件平台上（类似独立的操作系统，如VMWare ESXi）
* hosted hypervisor：
需要运行在宿主系统上（如VMWare Workstation, VirtualBox）

## Container (OS-level virtualization)

在操作系统的层次上对宿主机进行抽象和隔离。

核心：Container Manager，例如LXC, Docker

它通过OS内核的支持（如linux的chroot, cgroups, kernel namespace），将各种资源划分为若干独立的user space，分配给不同容器，使它们互不干扰。

## 虚拟机和容器两者比较

* 性能&资源开销<br>
虚拟机技术的资源开销更大，原因在于每台虚拟机中需要有单独的Guest OS，虚拟机中的系统调用需要通过hypervisor翻译成宿主机的指令完成。<br>
而对于容器技术，每个容器中没有单独的Guest OS，只需要包含应用及其运行环境即可。容器直接利用宿主系统的内核，容器中的系统调用会直接通过宿主系统的调用接口完成，无需翻译或模拟。<br>
显然也可以看出，通过容器技术实现的虚拟化在性能上优于虚拟机。

* Guest OS支持<br>
虚拟机技术支持在一台宿主机上运行多个不同平台的操作系统。<br>
对于容器技术，由于容器依赖于宿主系统的内核，故不同容器的系统平台都必须和宿主系统保持一致。

* 安全性<br>
虚拟机技术在硬件层次上进行抽象和隔离，而容器技术只在操作系统层次上进行，故宿主系统内核上的安全问题可能对容器的安全性造成威胁。<br>
由此，虚拟机在安全性上要优于容器技术。

## EX：简要比较LXC 和 Docker
LXC容器在功能上类似于一个完整的操作系统，在一个容器中往往包含多个应用。在这一点上，它更多地作为传统VM的替代使用。

Docker起初以LXC作为底层支持，后来单独开发了libcontainer替代LXC。
Docker容器面向应用，一个容器中只有一个应用。故它更加轻量、易于迁移和组合。
出于轻量级容器的考虑，Docker不允许数据的持久存储，故容器销毁时所有修改都不会被保存。如果要长期保存数据，则需要挂载宿主机的文件系统或使用外部存储。

## 利用LXC Python API的测试代码
https://github.com/cabbby/osprac/blob/master/%E7%AC%AC%E4%B8%80%E6%AC%A1%E4%BD%9C%E4%B8%9A/lxc_test.py

<br>

