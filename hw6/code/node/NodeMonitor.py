#!/usr/bin/env python3

import NodeProfile
import subprocess
import json
import time
import shutil
import os
import copy

class TaskList:
    def __init__(self):
        self.cnt = 0
        self.lst = []

    def add(self, job):
        task = {
            "taskId": self.cnt,
            "status": "Pending[A]",
            "containerId": "t%d-cont" % self.cnt,
            "name": job["name"], 
            "resource": job["resource"],
            "commandLine": job["commandLine"],
            "packagePath": job["packagePath"],
            "imageId": job["imageId"],
            "timeout": job["timeout"]
        }
        self.lst.append(task)
        self.cnt += 1
        return task

    def remove(self, taskId):
        for i in range(len(self.lst)):
            if self.lst[i]["taskId"] == taskId:
                resourceRem["mem"] -= self.lst[i]["resource"]["mem"]
                del(self.lst[i])

    def getInfo(self, taskId):
        for task in self.lst:
            if task["taskId"] == taskId:
                return {"code": 0, "data": {"containerId": task["containerId"], "status": task["status"]}}
        return {"code": 1}

    def kill(self, taskId):
        for i in range(len(self.lst)):
            if self.lst[i]["taskId"] == taskId:
                if self.lst[i]["status"] == "Running" or self.lst[i]["status"] == "Deploying":
                    self.lst[i]["process"].send_signal(subprocess.signal.SIGTERM)
                    '''
                    subprocess.call(["./delete-container", self.lst[i]["containerId"]])
                    self.lst[i]["status"] = "Killed"
                    '''
                    return {"code": 0}
                elif self.lst[i]["status"] == "Pending[A]":
                    self.lst[i]["status"] = "Killed"
                    return {"code": 0}
        return {"code": 1}

    
def fit(job):
    if len(job["resource"]["cpu"].split(',')) > resourceRem["cpu"]:
        return False
    if job["resource"]["mem"] > resourceRem["mem"]:
        return False
    return True

def getPath(taskId):
    return "/mnt/share/nodes/%d/task%d" % (nodeId, taskId)

def createTask(job):
    if fit(job):
        resourceRem["mem"] -= job["resource"]["mem"]
        task = taskList.add(job)
        shutil.rmtree(getPath(task["taskId"]), ignore_errors=True)
        task["process"] = subprocess.Popen(["python3", "TaskMonitor.py", json.dumps(task), "/mnt/share/nodes/%d" % nodeId])
        return {"code": 0, "data": {"taskId": task["taskId"]}}
    else:
        return {"code": 1}

def checkTaskStat(taskId):
    if not os.path.exists(getPath(taskId) + "/monitor_log"):
        return "Pending[A]"
    monitor_log = open(getPath(taskId) + "/monitor_log")
    lines = monitor_log.readlines()
    flag_deployed = False
    for line in lines:
        if "Finished" in line:
            return "Finished"
        if "Timeout" in line:
            return "Timeout"
        if "failed" in line:
            return "Failed"
        if "Killed" in line:
            return "Killed"
        if "deployed" in line:
            flag_deployed = True
    monitor_log.close()
    return "Running" if flag_deployed else "Deploying"

def loop():
    interval = 0.1
    while True:
        # update task status
        for task in taskList.lst:
            if not task["status"] in ["Finished", "Timeout", "Killed"]:
                task["status"] = checkTaskStat(task["taskId"])

        # update resource usage
        memUsed = 0
        for task in taskList.lst:
            if not task["status"] in ["Finished", "Timeout", "Failed", "Killed"]:
                print(task["status"])
                memUsed += task["resource"]["mem"]
        resourceRem["mem"] = resourceTot["mem"] - memUsed

        time.sleep(interval)

nodeId = NodeProfile.prof["nodeId"]
resourceTot = copy.copy(NodeProfile.prof["resourceTot"])
resourceRem = copy.copy(NodeProfile.prof["resourceTot"])

taskList = TaskList()