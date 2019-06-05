# import things
from flask_table import Table, Col, LinkCol
import MasterMonitor
import copy

# Declare your table
class RNodeTable(Table):
    nid = Col("NID")
    addr = Col("ADDR")
    cpu = Col('CPU')
    mem = Col('MEM')

def getTableHTML():
    # Populate the table
    lst = []
    for node in MasterMonitor.nodes:
        res = node.getResource()
        
        lst.append({
            "nid": node.nodeId,
            "addr": node.addr,
            "cpu": res["cpu"],
            "mem": res["mem"]
        })

    table = RNodeTable(lst)

    # Print the html
    return table.__html__()