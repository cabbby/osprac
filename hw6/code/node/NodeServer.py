#!/usr/bin/env python3

from flask import Flask, redirect, request, session, render_template
import NodeMonitor
import NodeProfile
import json
import threading
import sys

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, static_url_path='')
app.secret_key = "cabcatcarcapcan"

@app.before_first_request
def init():
    # NodeMonitor.init()
    pass

@app.route('/resource', methods=['GET'])
def getResource():
    return json.dumps(NodeMonitor.resourceRem)

@app.route('/task/info', methods=['GET'])
def getTaskInfo():
    result = NodeMonitor.taskList.getInfo(request.json["taskId"])
    return json.dumps(result)

@app.route('/task/create', methods=['POST'])
def createTask():
    result = NodeMonitor.createTask(request.json)
    return json.dumps(result)

@app.route('/task/kill', methods=['POST'])
def killTask():
    result = NodeMonitor.taskList.kill(request.json["taskId"])
    return json.dumps(result)

if __name__ == '__main__':
    monitor_thread = threading.Thread(target=NodeMonitor.loop)
    monitor_thread.start()
    app.run(host='0.0.0.0', port=int(sys.argv[1]))