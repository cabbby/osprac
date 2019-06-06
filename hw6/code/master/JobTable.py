# import things
from flask_table import Table, Col, LinkCol
import MasterMonitor
import copy

# Declare your table
class RJobTable(Table):
    jobId = Col("JID")
    nodeId = Col('NID')
    taskId = Col('TID')
    status = Col("Status")
    name = Col("Name")
    resource = Col("Resource")
    commandLine = Col("Command")
    packagePath = Col("Package")
    imageId = Col("Image")
    timeout = Col("Timeout")
    det = LinkCol("Details", "detail", url_kwargs=dict(jid="jobId"))
    kil = LinkCol("Kill", "kill", url_kwargs=dict(jid="jobId"))

def getTableHTML():
    # Populate the table
    lst = copy.copy(MasterMonitor.jobList.lst)
    table = RJobTable(lst)

    # Print the html
    return table.__html__()