#!/bin/bash
mkdir -p rootfs/bin
mkdir -p rootfs/usr/bin
mkdir -p rootfs/lib/x86_64-linux-gnu
mkdir -p rootfs/lib64/x86_64-linux-gnu
mkdir -p rootfs/usr/lib/x86_64-linux-gnu
mkdir -p rootfs/proc

cmds=(bash ls pwd echo cat rm mkdir)
ucmds=(stress vi)

for cmd in ${cmds[@]}; do 
	cp /bin/$cmd rootfs/bin 
done

for cmd in ${ucmds[@]}; do 
	cp /usr/bin/$cmd rootfs/usr/bin 
done

for cmd in ${cmds[@]}; do
    list="$(ldd /bin/$cmd | egrep -o '/lib.*\.[0-9]+')"
	for i in $list; do
		cp -v "$i" "./rootfs${i}";
	done
done

for cmd in ${ucmds[@]}; do
    list="$(ldd /usr/bin/$cmd | egrep -o '/lib.*\.[0-9]+|/usr/lib.*\.[0-9]+')"
	for i in $list; do
		cp -v "$i" "./rootfs${i}";
	done
done