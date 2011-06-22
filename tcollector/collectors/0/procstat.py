#!/usr/bin/python
import os, sys, getopt
MAINPATH=os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(MAINPATH+'lib/procmon')
import time
import socket
from constant import *
from metriclist import *
from procinfo import *
from report import *
from matcher import *
from procmon import *

def main():
  procmon = ProcMon()
  modules = [ProcInfoStat(), ProcInfoStatus(), ProcInfoIO()]
  for mod in modules:
    procmon.register_module(mod)
  reporters = [StdoutReporter()]
  for rep in reporters:
    procmon.register_reporter(rep)

  try:
    host = socket.gethostname()
  except:
    host = 'localhost'

  try:
    f = open(MAINPATH+"etc/procmon.conf", "r")
    conf = f.readlines()
    f.close()
  except:
    conf = []

  try:
    f = open(MAINPATH+"etc/mrtask.conf", "r")
    mrconf = f.readlines()
    f.close()
  except:
    mrconf = []

  matchers = [SubtreeMatcher(conf, host), MapReduceMatcher(mrconf, host), SumMatcher(host)]
  for mat in matchers:
    procmon.register_matcher(mat)
  procmon.initialize()
  procmon.run(10)

if __name__ == "__main__":
  main()
