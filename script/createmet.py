import os, subprocess

met = {}
f=open("metrics.txt", "r")
for l in f:
  items = l.split()
  if len(items[0]):
    met[items[0]] = 1

for k in met.keys():
  retcode = subprocess.call(['../src/tsdb', 'mkmetric', k])
