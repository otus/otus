#!/usr/bin/env python
import os
import sys
import time
import signal
import subprocess
MAINPATH=os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(MAINPATH+'lib/jmx')
import attribute
import reporter
import jmxdaemon
import crawl

if __name__ == '__main__':
  replist = reporter.ReporterList()
  attr = attribute.Attribute()
  attr.load(MAINPATH+"etc/jmx.conf")
  replist.config(attr)
  attr.set("jmxcmd", MAINPATH+'lib/jmx/jmxclient.jar')
  daemon = jmxdaemon.JMXDaemon(replist, attr)
  daemon.config(attr)
  while True:
    daemon.scan()
    time.sleep(10)
