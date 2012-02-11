import os, sys, time
#import rrdtool

class RRDReporter:
    def __init__(self, rrddir):
        self.step = 5;
        self.dir = rrddir
        try:
            os.makedirs(self.dir)
        except:
            pass
        self.now = int(time.time()) / self.step * self.step

    def create(self, filename):
        if os.path.exists(filename):
            return
        try:
            ret = rrdtool.create(filename,
                "--step", str(self.step), "--start", str(self.now-10),
                "DS:sum:GAUGE:20:U:U",
                "RRA:AVERAGE:0.5:1:181440",
                "RRA:AVERAGE:0.5:12:181440")
        except:
            pass

    def startGroup(self):
        pass

    def report(self, name, timestamp, value, tags):
        filename = self.dir+name+".rrd"
        self.create(filename)
        try:
            rrdtool.update(filename, str(timestamp/self.step*self.step)+":"+str(value))
        except:
            pass

    def endGroup(self):
        pass

    def graph(self, name):
        filename = dir+name+".rrd"
        rrdtool.graph("debug.png", "--start", "-3600",
              "DEF:ino=net.rrd:input:AVERAGE",
              "AREA:ino#00FF00:In traffic")

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
        try:
            os.system(cmdExec)
        except:
            sys.stderr.write("gmetric reporter sends result error")

    def startGroup(self):
        pass

    def report(self, name, timestamp, val, tags):
        self.sendToGmetric(name, val)

    def endGroup(self):
        pass

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
            sys.stderr.write(str(e))
            sys.stderr.write("logger reporter open log file error")
            self.logger = None

    def checkLogger(self, nowtime):
        if nowtime - self.logFlushTime > 60:
            self.logFlushTime = nowtime
            try:
                self.logger.flush()
            except IOError, e:
                sys.stderr.write(str(e))
                sys.stderr.write("logger reporter check logger error")
        newdate = time.strftime("%Y-%m-%d", time.localtime())
        if self.date != newdate:
            self.openLogFile(newdate)

    def report(self, name, timestamp, val, tags):
        try:
            self.logger.write("%s %s\n"%(name, str(val)))
        except IOError, e:
            sys.stderr.write(str(e))
            sys.stderr.write("logger reporter report write error")

    def startGroup(self):
        nowtime = time.time()
        self.checkLogger(nowtime)
        try:
            self.logger.write("%d\n"%(nowtime));
        except IOError, e:
            sys.stderr.write(str(e))
            sys.stderr.write("logger reporter start group error")

    def endGroup(self):
        pass

class StdoutReporter:
    def startGroup(self):
        pass

    def hasType(self):
        return True

    def report(self, name, timestamp, val, tags):
        print "%s %d %s %s"%(name, timestamp, str(val), tags)

    def endGroup(self):
        sys.stdout.flush()

class ReporterList:
    def __init__(self):
        self.list = []

    def init1(self, cmdGmetric, logFileDir):
        self.add(GmetricReporter(cmdGmetric))
        self.add(LoggerReporter(logFileDir))

    def init2(self, attr):
        self.add(GmetricReporter(attr.get("gmetriccmd", "gmetric")))
        self.add(StdoutReporter())

    def add(self, reporter):
        self.list.append(reporter)

    def startGroup(self):
        for rep in self.list:
            rep.startGroup()

    def reportLogger(self, name, timestamp, value, tags):
        self.list[1].report(name, timestamp, value, tags)

    def report(self, name, timestamp, value, tags):
        for rep in self.list:
            rep.report(name, timestamp, value, tags)

    def endGroup(self):
        pass
