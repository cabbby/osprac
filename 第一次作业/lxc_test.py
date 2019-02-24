#!/usr/bin/python3
import lxc
import sys

# Setup the container object
c = lxc.Container("cab-container")
if c.defined:
    print("Container already exists", file=sys.stderr)
    sys.exit(1)

# Create the container rootfs
if not c.create("download", lxc.LXC_CREATE_QUIET, {"dist": "debian",
                                                   "release": "stretch",
                                                   "arch": "i386"}):
    print("Failed to create the container rootfs", file=sys.stderr)
    sys.exit(1)

# Start the container
if not c.start():
    print("Failed to start the container", file=sys.stderr)
    sys.exit(1)

# Query some information
print("Container state: %s" % c.state)
print("Container PID: %s" % c.init_pid)

# Create the file
c.attach_wait(lxc.attach_run_command, ["bash", "-c", "echo \"魏龙 1700012905\" > /Hello-Container"])
c.attach_wait(lxc.attach_run_command, ["bash", "-c", "cat < /Hello-Container"])

# Stop the container
if not c.stop():
    print("Failed to stop the container", file=sys.stderr)