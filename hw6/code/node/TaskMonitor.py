#!/usr/bin/env python3

import os
import sys
import time
import json
import subprocess
import shutil
import signal

class Killer:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit)
    signal.signal(signal.SIGTERM, self.exit)

  def exit(self, signum, frame):
    self.kill_now = True


def writeLog(str):
    monitor_log = open(node_root + "/task%d/monitor_log" % task["taskId"], "a")
    monitor_log.write(str + "\n")
    monitor_log.close()

if __name__ == "__main__":
    task = json.loads(sys.argv[1])
    node_root = sys.argv[2]
    killer = Killer()

    taskId = task["taskId"]

    if not os.path.exists(node_root + "/task%d" % taskId):
        os.makedirs(node_root + "/task%d" % taskId)

    monitor_log = open(node_root + "/task%d/monitor_log" % taskId, "w")
    monitor_log.write("Monitor started\n")
    monitor_log.close()

    task_stdout = open(node_root + "/task%d/task_stdout" % taskId, "w")
    task_stderr = open(node_root + "/task%d/task_stderr" % taskId, "w")

    containerId = "t%d-cont" % task["taskId"]
    writeLog("Trying to create container")
    code = subprocess.call(["./create-container", containerId, task["resource"]["cpu"], str(task["resource"]["mem"] << 20), task["imageId"]], stdout=None, stderr=None)
    if code:
        writeLog("Container failed to create: %d" % code)
    else:
        writeLog("Container created successfully")

        for path in task["packagePath"].split(";"):
            if os.path.isdir(path):
                shutil.copytree(path, "/root/cont/%s/usrfile/workspace/" % containerId)
                writeLog("%s copied to container" % path)
            elif os.path.isfile(path):
                shutil.copy(path, "/root/cont/%s/usrfile/workspace/" % containerId)
                writeLog("%s copied to container" % path)

        writeLog("Container deployed successfully")

        interval = 0.1
        startTime = time.time()
        s = subprocess.Popen(["lxc-attach", "-n", containerId, "--", "/bin/bash", "-c", "cd /workspace && " + task["commandLine"]], stdout=task_stdout, stderr=task_stderr)
        while True:
            pastTime = time.time() - startTime

            if killer.kill_now:
                writeLog("[%.3f] Killed" % pastTime)
                break

            if s.poll() is not None:
                if s.returncode:
                    writeLog("[%.3f] Command failed to execute: %d" % (pastTime, s.returncode))
                else:
                    writeLog("[%.3f] Finished" % pastTime)
                break
            if task["timeout"] < 1000 * pastTime:
                writeLog("[%.3f] Timeout" % pastTime)
                s.terminate()
                break
            time.sleep(interval)

        code = subprocess.call(["./delete-container", containerId], stdout=None, stderr=None)
        if code:
            writeLog("Container failed to delete: %d" % code)
        else:
            writeLog("Container deleted successfully")
        

    task_stdout.close()
    task_stderr.close()