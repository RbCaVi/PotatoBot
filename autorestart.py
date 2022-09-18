import subprocess
import time
import os
import sys

file=sys.argv[1]
lastmodified=os.path.getmtime(file)
process=subprocess.Popen(["python3",file], shell=False)
while True:
	process.poll()
	lastmodified2=os.path.getmtime(file)
	if lastmodified2>lastmodified or process.returncode is not None:
		print("Restarting...")
		process.send_signal(subprocess.signal.SIGINT)
		process.wait()
		process=subprocess.Popen(["python3",file], shell=False)
		lastmodified=lastmodified2