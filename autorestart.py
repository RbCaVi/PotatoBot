import subprocess
import time
import os
import sys

file=sys.argv[1]
lastmodified=os.path.getmtime(file)
process=subprocess.Popen(["python3",file], shell=False)
while True:
	lastmodified2=os.path.getmtime(file)
	if lastmodified2>lastmodified:
		print("Restarting...")
		process.send_signal(subprocess.signal.SIGINT)
		process.wait()
		process=subprocess.Popen(["python3",file], shell=False)