#!/usr/bin/env python
import os, sys, getopt
MAINPATH=os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(MAINPATH+'lib/')
import time
import socket
from procmon import procmon
from procmon import config
from procmon import procinfo
from procmon import reporter
from procmon import matcher
from procmon import config

def main():
  procmonitor = procmon.ProcMon()
  modules = [procinfo.ProcInfoStat(), procinfo.ProcInfoStatus(),
             procinfo.ProcInfoIO()]
  for mod in modules:
    procmonitor.register_module(mod)
  reporters = [reporter.StdoutReporter()]
  for rep in reporters:
    procmonitor.register_reporter(rep)

  try:
    host = socket.gethostname()
  except:
    host = 'localhost'

  config_parser = config.ProcmonConfigParser()
  procconf = config_parser.load_procmon_config(MAINPATH+'etc/procmon.xml')
  mrconf = config_parser.load_mrtask_config(MAINPATH+'etc/mrtask.xml')
  matchers = [matcher.SubtreeMatcher(procconf, host),
              matcher.MapReduceMatcher(mrconf, host),
              matcher.SumMatcher(host)]
  for mat in matchers:
    procmonitor.register_matcher(mat)
  procmonitor.initialize()
  procmonitor.run(10)

if __name__ == "__main__":
  main()
