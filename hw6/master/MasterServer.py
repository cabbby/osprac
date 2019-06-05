#!/usr/bin/env python3
from flask import Flask, redirect, request, session, render_template, Response
import MasterMonitor, JobTable, NodeTable, threading, sys, json, shutil
from multiprocessing import Process

app = Flask(__name__, static_url_path='')
app.secret_key = "cabcatcarcapcan"

@app.before_first_request
def init():
    pass

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html', jobList=JobTable.getTableHTML(), nodeList=NodeTable.getTableHTML())

@app.route('/job/create', methods=['POST'])
def createJob():
    form = request.form
    MasterMonitor.createJob(form["name"], {"cpu": form["cpu"], "mem": int(form["mem"])}, form["cmdline"], form["pkgpath"], form["imgid"], int(form["timeout"]))
    return redirect("/")

@app.route('/job/create_json', methods=['POST'])
def createJob_json():
    lst = json.loads(request.form["json"])
    for entry in lst:
        MasterMonitor.createJob(entry["name"], entry["resource"], entry["commandLine"], entry["packagePath"], entry["imageId"], entry["timeout"])
    return redirect("/")

@app.route('/job/details/<int:jid>', methods=['GET'])
def detail(jid):
    t = MasterMonitor.jobList.getDetails(jid)
    return render_template("details.html", job=json.dumps(t["job"]), task_stdout=format(t["task_stdout"]), task_stderr=format(t["task_stderr"]), monitor_log=format(t["monitor_log"]))

@app.route('/job/kill/<int:jid>', methods=['GET', 'POST'])
def kill(jid):
    MasterMonitor.jobList.killJob(jid)
    return redirect("/")

@app.route('/job/table', methods=['GET'])
def getJobTable():
    return Response(JobTable.getTableHTML())

def format(lines):
    text = ""
    for line in lines:
        text += line
    return text

if __name__ == '__main__':
    shutil.rmtree("/mnt/share/nodes", ignore_errors=True)
    monitor_thread = threading.Thread(target=MasterMonitor.loop)
    monitor_thread.start()
    app.run(host='0.0.0.0', port=int(sys.argv[1]))