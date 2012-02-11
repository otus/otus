import sys
from constant import *

def getCmdLine(pid):
    try:
        f = open(PATH.PROCPID_CMDLINE%(pid), 'r');
        lines = f.readlines()
        f.close()
        ret = ''.join(lines)
    except:
        return ''
    return ret

def getPPidAndUid(pid):
    try:
        f = open(PATH.PROCPID_STATUS%(pid), 'r');
        lines = f.readlines();
        f.close()
    except Exception, e:
        sys.stderr.write(str(e))
        return (None, None)
    ppid = 1
    uid = 0
    for line in lines:
        items = line.split()
        if items[0].startswith("PPid"):
            ppid = int(items[1])
        if items[0].startswith("Uid"):
            uid = int(items[1])
    return (ppid, uid)

class ProcInfoStat:
    SIZE = 4
    INDEX = [13, 14]

    def __init__(self):
        try:
            f = open("/proc/stat", "r")
            self.numP = 0
            for l in f:
                if l.startswith("cpu"):
                    self.numP += 1
            if self.numP > 1:
                self.numP -= 1
        except:
            self.numP = 0

    def size(self):
        return ProcInfoStat.SIZE

    def naming(self):
        return ["cpu_user_time", "cpu_system_time", "cpu_user", "cpu_system"]

    def update(self, pid, met, intv):
        try:
            f = open(PATH.PROCPID_STAT%(pid), 'r');
            line = f.readline()
            f.close()
        except Exception, e:
            sys.stderr.write(str(e))
            return
        items = line.split()
        i = 0
        for ind in ProcInfoStat.INDEX:
            newmet = float(items[ind]) / self.numP
            if met[i] >= 0:
                met[i+2] = (newmet - met[i]) / intv
            else:
                met[i+2] = 0
            met[i] = newmet
            i += 1

class ProcInfoIO:
    SIZE = 6

    def size(self):
        return ProcInfoIO.SIZE

    def naming(self):
        return ["readbytes", "writebytes", "canwritebytes", \
                        "readbytesrate", "writebytesrate", "canwritebytesrate"]

    def update(self, pid, met, intv):
        try:
            f = open(PATH.PROCPID_IO%(pid), 'r');
            lines = f.readlines();
            f.close()
        except Exception, e:
            sys.stderr.write(str(e))
            return
        for i in range(3):
            newmet = float(lines[4+i].split()[1])
            if met[i] >= 0:
                met[i+3] = (newmet - met[i]) / intv
            else:
                met[i+3] = 0
            met[i] = newmet

class ProcInfoStatus:
    SIZE = 2

    def size(self):
        return ProcInfoStatus.SIZE

    def naming(self):
        return ["vmsize", "vmrss"]

    def update(self, pid, met, intv):
        try:
            f = open(PATH.PROCPID_STATUS%(pid), 'r');
            lines = f.readlines();
            f.close()
        except Exception, e:
            sys.stderr.write(str(e))
            return
        met[0] = 0
        met[1] = 0
        for line in lines:
            items = line.split()
            if items[0].startswith("VmSize"):
                met[0] = long(items[1]) * 1024
            if items[0].startswith("VmRSS"):
                met[1] = long(items[1]) * 1024
