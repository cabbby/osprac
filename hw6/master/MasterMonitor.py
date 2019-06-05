#!/usr/bin/env python3
import MasterProfile, MasterServer, json, requests, time

class Node:
    def __init__(self, nodeId, addr):
        self.nodeId = nodeId
        self.addr = addr

    def getResource(self):
        r = requests.get("http://%s/resource" % self.addr)
        return r.json()

    def getTaskInfo(self, taskId):
        r = requests.get("http://%s/task/info" % self.addr, json={"taskId": taskId})
        return r.json()

    def fit(self, job):
        r = self.getResource()
        return len(job["resource"]["cpu"].split(',')) <= r["cpu"] and job["resource"]["mem"] <= r["mem"]

    def submitJob(self, job):
        r = requests.post("http://%s/task/create" % self.addr, json=job)
        return r.json()

    def killTask(self, taskId):
        r = requests.post("http://%s/task/kill" % self.addr, json={"taskId": taskId})
        return r


class JobList:
    def __init__(self):
        self.cnt = 0
        self.lst = []

    def add(self, name, resource, commandLine, packagePath, imageId, timeout):
        job = {
            "jobId": self.cnt,
            "status": "Pending[ ]",
            "nodeId": -1,
            "taskId": -1,
            "name": name, 
            "resource": resource, 
            "commandLine": commandLine, 
            "packagePath": packagePath, 
            "imageId": imageId, 
            "timeout": timeout
            }
        self.lst.append(job)
        self.cnt += 1
        return job

    def remove(self, id):
        for i in range(len(self.lst)):
            if self.lst[i]["jobId"] == id:
                del(self.lst[i])
                return True
        return False

    def updateInfo(self):
        for job in self.lst:
            if job["nodeId"] == -1:
                assign(job)
            else:
                info = nodes[job["nodeId"]].getTaskInfo(job["taskId"])
                if info["code"] == 0:
                    job["status"] = info["data"]["status"]
                else:
                    print("error requiring info for job %d" % job["jobId"])

    def getDetails(self, jobId):
        for job in self.lst:
            if job["jobId"] == jobId:
                return {
                    "job": job,
                    "monitor_log": readFile(job, "monitor_log"),
                    "task_stdout": readFile(job, "task_stdout"),
                    "task_stderr": readFile(job, "task_stderr")
                }

    def killJob(self, jobId):
        for job in self.lst:
            if job["jobId"] == jobId:
                ret = nodes[job["nodeId"]].killTask(job["taskId"])


def readFile(job, fn):
    f = open("/mnt/share/nodes/%d/task%d/%s" % (job["nodeId"], job["taskId"], fn))
    return f.readlines()

def assign(job):
    best = 0
    for i in range(0, len(nodes)):
        if nodes[i].getResource()["mem"] > nodes[best].getResource()["mem"]:
            best = i

    if best.fit(job):
        job["nodeId"] = nodes[best].nodeId
        job["status"] = "Pending[A]"
        ret = nodes[best].submitJob(job)
        job["taskId"] = ret["data"]["taskId"]
        return True

    return False

def createJob(name, resource, commandLine, packagePath, imageId, timeout):
    jobList.add(name, resource, commandLine, packagePath, imageId, timeout)
    return False

def getNodesInfo():
    res = []
    for node in nodes:
        res.append(node.getResource())
    return res

nodes = []
jobList = JobList()
for entry in MasterProfile.prof["nodes"]:
    nodes.append(Node(entry["nodeId"], entry["addr"]))

def loop():
    interval = 0.1
    while True:
        jobList.updateInfo()
        time.sleep(interval)
