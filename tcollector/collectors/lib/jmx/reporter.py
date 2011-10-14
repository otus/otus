import os, time

class GmetricReporter:
  def __init__(self, _cmdGmetric):
    self.cmdGmetric = _cmdGmetric

  def sendToGmetric(self, name, val, group="database", mtype="float", \
      tmax=20, dmax=10):
    cmdExec = self.cmdGmetric \
            + " --name="  + name \
            + " --value=" + str(val) \
            + " --group=" + group \
            + " --type="  + mtype \
            + " --tmax="  + str(tmax) \
            + " --dmax="  + str(dmax)
    global debug
    if debug == 1:
      print "cmdExec="+cmdExec
    try:
      os.system(cmdExec)
    except:
      print "gmetric reporter sends result error"

  def report(self, name, timestamp, val, tags):
    self.sendToGmetric(name, val)

  def startGroup(self):
    pass

  def endGroup(self):
    pass

class StdoutReporter:
  def startGroup(self):
    pass

  def hasType(self):
    return True

  def report(self, name, timestamp, val, tags):
    print "%s %s %s %s"%(name, str(timestamp), str(val), tags)

  def endGroup(self):
    sys.stdout.flush()

class LoggerReporter:
  def __init__(self, _logFileDir):
    self.logFileDir = _logFileDir
    self.logger = None
    self.openLogFile(time.strftime("%Y-%m-%d", time.localtime()))
    self.logFlushTime = 0

  def openLogFile(self, newdate):
    self.date = newdate
    try:
      if self.logger is not None:
        self.logger.close()
      self.logger = open("%s-%s.log"%(self.logFileDir, newdate) , "a")
    except IOError, e:
      print e
      print "logger reporter open log file error"
      self.logger = None

  def checkLogger(self, nowtime):
    if nowtime - self.logFlushTime > 60:
      self.logFlushTime = nowtime
      try:
        self.logger.flush()
      except IOError, e:
        print e
        print "logger reporter check logger error"
    newdate = time.strftime("%Y-%m-%d", time.localtime())
    if self.date != newdate:
      self.openLogFile(newdate)

  def report(self, name, timestamp, val, tags):
    try:
      self.logger.write("%s %s %s %s\n"%(name, str(timestamp), str(val), tags))
    except IOError, e:
      print e
      print "logger reporter report write error"

  def startGroup(self):
    nowtime = time.time()
    self.checkLogger(nowtime)

  def endGroup(self):
    pass

class ReporterList:
  def __init__(self):
    self.list = []

  def config(self, attr):
    rep_list = attr.get("reporters", "stdout")
    if rep_list.find('gmetric') >= 0:
      self.add(GmetricReporter(attr.get("gmetriccmd", "gmetric")))
    if rep_list.find('logger') >= 0:
      self.add(LoggerReporter(attr.get("logdir", "./")))
    if rep_list.find('stdout') >= 0:
      self.add(StdoutReporter())

  def add(self, reporter):
    self.list.append(reporter)

  def startGroup(self):
    for rep in self.list:
      rep.startGroup()

  def report(self, name, timestamp, value, tags=""):
    for rep in self.list:
      rep.report(name, timestamp, value, tags)

  def endGroup(self):
    for rep in self.list:
      rep.endGroup()
