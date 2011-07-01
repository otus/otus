import re
#import json
import socket
import sys
from constant import *
from metriclist import *
from procinfo import *
from procmon import *
from report import *

class SubtreeMatcher:
  #rule definition:
  #pid, uid, cmdline, agg_sub_tree, nameschema
  RULE_LEN = 5
  RULE_IND_PID = 0
  RULE_IND_UID = 1
  RULE_IND_CMD = 2
  RULE_IND_AGG = 3
  RULE_IND_NAME = 4
  RULE_IND_NUID = 5
  RULEKEYTOID = {'pid':RULE_IND_PID, 'uid':RULE_IND_UID,\
    'cmd':RULE_IND_CMD, 'agg':RULE_IND_AGG, \
    'name':RULE_IND_NAME, 'nuid':RULE_IND_NUID}

  def __init__(self, conf, _host):
    self.parseRules(conf)
    self.results = []
    self.modules = None
    self.host = _host

  def parseRules(self, conf):
    self.rules = []
    try:
      for l in conf:
        nrule = [0, 0, '', False, '', 0]
        items = l.split()
        i = 0
        while (i < len(items)):
          id = self.RULEKEYTOID[items[i]]
          if isinstance(nrule[id], int):
            nrule[id] = int(items[i+1])
          elif isinstance(nrule[id], bool):
            nrule[id] = bool(items[i+1])
          else:
            nrule[id] = items[i+1]
          i = i + 2
        self.rules.append(nrule)
    except:
      sys.stderr.write("Parse rule configuration failed.")
      self.rules = []

  '''
  def parseRules(self, conf):
    raw_rules = loads(conf)
    self.rules = []
    try:
      for rule in raw_rules:
        nrule = [0, 0, '', False, '', 0]
        for key in rule.keys():
          nrule[self.RULEKEYTOID[key]] = rule[key]
        self.rules.append(nrule)
    except:
      sys.stderr.write("Parse rule configuration failed.")
      self.rules = []
  '''

  def initMetric(self, modules):
    self.results = []
    self.modules = modules
    for i in range(0, len(self.rules)):
      self.results.append(MetricList(modules, 0))

  def startGroup(self):
    for i in range(0, len(self.rules)):
      self.results[i].setZero()

  def getMetric(self, proc):
    return proc.getMetric()

  def aggTree(self, pinfo, result):
    tree = pinfo.get_subtree()
    for pid in tree:
      proc = pinfo.plist.procs[pid]
      result.add(self.getMetric(proc))

  def check(self, pinfo):
    for i in range(0, len(self.rules)):
      rule = self.rules[i]
      if rule[self.RULE_IND_PID] > 0 and rule[self.RULE_IND_PID] != pinfo.pid:
        continue
      if rule[self.RULE_IND_UID] > 0 and rule[self.RULE_IND_UID] != pinfo.uid:
        continue
      if rule[self.RULE_IND_NUID] > 0 and rule[self.RULE_IND_NUID] == pinfo.uid:
        continue
      if rule[self.RULE_IND_CMD] != '' and \
         not re.match(rule[self.RULE_IND_CMD], pinfo.cmd):
        continue
      if rule[self.RULE_IND_AGG]:
        self.aggTree(pinfo, self.results[i])
      else:
        self.results[i].add(self.getMetric(pinfo))

  def report(self, timestamp, reporter):
    for i in range(0, len(self.rules)):
      for j in range(0, len(self.modules)):
        module = self.modules[j]
        for k in range(0, module.size()):
          name = "process.%s" % (module.naming()[k])
          types = "proc=%s"%(self.rules[i][self.RULE_IND_NAME])
          value = self.results[i].get(j, k)
          reporter.report(name, timestamp, value, types)

  def endGroup(self):
    pass

  def listMetricName(self):
    names = []
    for i in range(0, len(self.rules)):
      for j in range(0, len(self.modules)):
        module = self.modules[j]
        for k in range(0, module.size()):
          name = "%s.%s"%(self.rules[i][self.RULE_IND_NAME], module.naming()[k])
          names.append(str(name))
    return names

class MRManager:
  def __init__(self, numTask, taskType):
    self.numTask = numTask
    self.taskType = taskType
    self.tasks = [['',None]]* self.numTask
    self.nactive = 0

  def cleanUpdateList(self):
    self.updateList = []

  def updateProc(self, taskid, pinfo):
    self.updateList.append([taskid, pinfo])

  def update(self):
    mark = [True] * len(self.updateList)
    for i in range(self.numTask):
      mid = self.tasks[i][0]
      find = False
      pinfo = None
      for j in range(len(self.updateList)):
        if mark[j] and self.updateList[j][0] == mid:
          pinfo = self.updateList[j][1]
          mark[j] = False
          find = True
          break
      if find:
        self.tasks[i][1] = pinfo
        continue
      find = False
      for j in range(len(self.updateList)):
        if mark[j]:
          self.tasks[i] = self.updateList[j]
          mark[j] = False
          find = True
          break
      if not find:
        self.tasks[i][0]=''

    self.nactive = self.numTask
    for j in range(len(self.updateList)):
      if mark[j]:
        if self.nactive < len(self.tasks):
          self.tasks[self.nactive] = self.updateList[j]
        else:
          self.tasks.append(self.updateList[j])
        self.nactive += 1

  def report(self, modules, timestamp, reporter):
    for i in range(self.nactive):
      if self.tasks[i][0] != '':
        taskid = self.tasks[i][0]
        pinfo = self.tasks[i][1]
        agg = pinfo.getAggTreeMetric()
        for j in range(0, len(modules)):
          module = modules[j]
          for k in range(0, module.size()):
            name = "mrjob.%s" % (module.naming()[k])
            types = "jobid=%s tasktype=%s%d taskid=%s" \
                %(taskid[0:17], self.taskType, i, taskid[20:29])
            value = agg.get(j, k)
            reporter.report(name, timestamp, value, types)

class MapReduceMatcher(SubtreeMatcher):
  #rule definition:
  #pid, uid, cmdline, agg_sub_tree, nameschema
  RULE_LEN = 5
  RULE_IND_PID = 0
  RULE_IND_UID = 1
  RULE_IND_CMD = 2
  RULE_IND_AGG = 3
  RULE_IND_NAME = 4
  RULE_IND_NUID = 5
  RULE_IND_NMAPPER = 6
  RULE_IND_NREDUCER = 7
  RULEKEYTOID = {'pid':RULE_IND_PID, 'uid':RULE_IND_UID,\
    'cmd':RULE_IND_CMD, 'agg':RULE_IND_AGG, \
    'name':RULE_IND_NAME, 'nuid':RULE_IND_NUID, \
    'nmapper':RULE_IND_NMAPPER, 'nreducer':RULE_IND_NREDUCER}

  def __init__(self, conf, _host):
    self.parseRules(conf)
    self.managers = []
    for i in range(len(self.rules)):
      self.managers.append(MRManager(self.rules[i][self.RULE_IND_NMAPPER], 'm'))
      self.managers.append(MRManager(self.rules[i][self.RULE_IND_NREDUCER], 'r'))
    self.host = _host

  def parseRules(self, conf):
    self.rules = []
#    try:
    for l in conf:
      nrule = [0, 0, '', False, '', 0, 0, 0]
      items = l.split()
      i = 0
      while (i < len(items)):
        id = self.RULEKEYTOID[items[i]]
        if isinstance(nrule[id], int):
          nrule[id] = int(items[i+1])
        elif isinstance(nrule[id], bool):
          nrule[id] = bool(items[i+1])
        else:
          nrule[id] = items[i+1]
        i = i + 2
      self.rules.append(nrule)
#    except:
#      sys.stderr.write("Parse rule configuration failed.")
#      self.rules = []

  def initMetric(self, modules):
    self.results = []
    self.modules = modules

  def startGroup(self):
    for manager in self.managers:
      manager.cleanUpdateList()

  def check(self, pinfo):
    for i in range(0, len(self.rules)):
      rule = self.rules[i]
      if rule[self.RULE_IND_PID] > 0 and rule[self.RULE_IND_PID] != pinfo.pid:
        continue
      if rule[self.RULE_IND_UID] > 0 and rule[self.RULE_IND_UID] != pinfo.uid:
        continue
      if rule[self.RULE_IND_NUID] > 0 and rule[self.RULE_IND_NUID] == pinfo.uid:
        continue
      if rule[self.RULE_IND_CMD] != '' and \
         not re.match(rule[self.RULE_IND_CMD], pinfo.cmd):
        continue
      prefix = "-Dhadoop.tasklog.taskid=attempt"
      pos = pinfo.cmd.find(prefix)
      if pos >= 0:
        taskid = pinfo.cmd[pos+len(prefix)+1:pos+len(prefix)+29]
        if taskid[18] == 'm':
          self.managers[i*2].updateProc(taskid, pinfo)
        else:
          self.managers[i*2+1].updateProc(taskid, pinfo)

  def endGroup(self):
    for manager in self.managers:
      manager.update()

  def report(self, timestamp, reporter):
    for manager in self.managers:
      manager.report(self.modules, timestamp, reporter)

  def listMetricName(self):
    names = []
    for i in range(0, len(self.rules)):
      for j in range(0, len(self.modules)):
        module = self.modules[j]
        for k in range(0, module.size()):
          name = "mrjob.%s"%(module.naming()[k])
          names.append(str(name))
    return names

class SubtreeRateMatcher(SubtreeMatcher):
  def getMetric(self, proc):
    return proc.getRate()

class SumMatcher:
  def __init__(self, _host):
    self.metrics = []
    self.modules = None
    self.host = _host

  def initMetric(self, modules):
    self.modules = modules
    self.metrics = MetricList(modules, 0)

  def startGroup(self):
    self.metrics.setZero()

  def getMetric(self, proc):
    return proc.getMetric()

  def check(self, pinfo):
    self.metrics.add(self.getMetric(pinfo))

  def report(self, timestamp, reporter):
    for i in range(0, len(self.modules)):
      module = self.modules[i]
      for j in range(0, module.size()):
        name = "node.%s" % (module.naming()[j])
        value= self.metrics.get(i, j)
        reporter.report(name, timestamp, value, "")

  def endGroup(self):
    pass

  def listMetricName(self):
    names = []
    for i in range(0, len(self.modules)):
      module = self.modules[i]
      for j in range(0, module.size()):
        name = "node.%s"%(module.naming()[j])
        names.append(name)
    return names

def test1():
  PATH.PROCPID_CMDLINE='./test/proc/%d/cmdline'
  PATH.PROCPID_STATUS='./test/proc/%d/status'
  PATH.PROCPID_STAT='./test/proc/%d/stat'
  PATH.PROCPID_IO='./test/proc/%d/io'

  f = open("./test/conf1.txt", "r")
  lines = f.readlines()
  f.close()
  conf = ''
  for line in lines:
    conf += line
  matcher = SubtreeMatcher(conf)
  modules = [ProcInfoStat(), ProcInfoStatus(), ProcInfoIO()]
  summat  = SumMatcher()
  matcher.initMetric(modules)
  summat.initMetric(modules)
  print matcher.listMetricName()
  print summat.listMetricName()

  plist = {}
  proc = ProcInfo(1, plist, modules)
  plist[1] = proc
  proc.update(0)
  matcher.startGroup()
  matcher.check(proc)
  stdoutr = StdoutReporter()
  matcher.report(2, stdoutr)

  proc.update(5)
  matcher.startGroup()
  matcher.check(proc)
  matcher.report(2, stdoutr)

def test2():
  f = open("./test.txt", "r")
  conf = f.readlines()
  f.close()
  matcher = SubtreeMatcher(conf, "localhost")
  modules = [ProcInfoStat(), ProcInfoStatus(), ProcInfoIO()]
  matcher.initMetric(modules)
  plist = {}
  pid = 1856
  proc = ProcInfo(pid, plist, modules)
  plist[pid] = proc
  proc.update(0)
  matcher.startGroup()
  matcher.check(proc)
  stdoutr = StdoutReporter()
  matcher.report(2, stdoutr)

def test3():
  f = open("./mrtask.conf", "r")
  conf = f.readlines()
  f.close()
  matcher = MapReduceMatcher(conf, "localhost")
  modules = [ProcInfoStat(), ProcInfoStatus(), ProcInfoIO()]
  matcher.initMetric(modules)
  plist = ProcMon()
  pid = 30538 
  proc = ProcInfo(pid, plist, modules)
  plist.procs[pid] = proc
  proc.update(0)
  proc.prepare_tree()
  #proc.cmd = "4j12-1.4.3.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/commons-el-1.0.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/core-3.1.1.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/servlet-api-2.5-6.1.14.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/jetty-6.1.14.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/log4j-1.2.15.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/slf4j-api-1.4.3.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/xmlenc-0.52.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/jets3t-0.6.1.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/commons-cli-1.2.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/commons-httpclient-3.0.1.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/jasper-runtime-5.5.12.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/jetty-util-6.1.14.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/junit-3.8.1.jar::/l/b2/scratch/hadoop-data/global/mapred/local/taskTracker/jobcache/job_201106031747_0066/jars/classes:/l/b2/scratch/hadoop-data/global/mapred/local/taskTracker/jobcache/job_201106031747_0066/jars:/l/d2/scratch/hadoop-data/global/mapred/local/taskTracker/jobcache/job_201106031747_0066/attempt_201106031747_0066_r_000000_1/work -Dhadoop.log.dir=/l/a2/scratch/hadoop-data/global/log -Dhadoop.root.logger=INFO,TLA -Dhadoop.tasklog.taskid=attempt_201106031747_0066_r_000000_1 -Dhadoop.tasklog.totalLogFileSize=0 org.apache.hadoop.mapred.Child 127.0.0.1 44373 attempt_201106031747_0066_r_000000_1 -1985077290"
  matcher.startGroup()
  matcher.check(proc)
  matcher.endGroup()
  stdoutr = StdoutReporter()
  matcher.report(2, stdoutr)

if __name__ == '__main__':
  test3()
