import re
#import json
import socket
import sys
from constant import *
from metriclist import *
from procinfo import *
from procmon import *
from reporter import *

def safe_get(dictionary, key):
    if key in dictionary:
        return dictionary[key]
    else:
        return None

class SubtreeMatcherRule:
    RULE_LEN      = 6
    RULE_IND_PID  = 0
    RULE_IND_UID  = 1
    RULE_IND_CMD  = 2
    RULE_IND_AGG  = 3
    RULE_IND_NAME = 4
    RULE_IND_NUID = 5
    RULEKEYTOID = { \
        'pid':RULE_IND_PID, 'uid':RULE_IND_UID, \
        'cmd':RULE_IND_CMD, 'agg':RULE_IND_AGG, \
        'name':RULE_IND_NAME, 'nuid':RULE_IND_NUID \
    }

    def __init__(self):
        self._rule = [0, 0, '', False, '', 0]

    def set_rule(self, conf):
        pid = safe_get(conf, 'pid')
        if pid is not None and pid.isdigit():
            self._rule[self.RULE_IND_PID] = int(pid)
        uid = safe_get(conf, 'uid')
        if uid is not None and uid.isdigit():
            self._rule[self.RULE_IND_UID] = int(uid)
        cmd = safe_get(conf, 'cmdline')
        if cmd is not None:
            self._rule[self.RULE_IND_CMD] = cmd
        agg = safe_get(conf, 'aggregated')
        if agg is not None and (agg == 'True' or agg == 'False'):
            self._rule[self.RULE_IND_AGG] = bool(agg)
        name = safe_get(conf, 'displayname')
        if name is not None:
            self._rule[self.RULE_IND_NAME] = name
        nuid = safe_get(conf, 'nuid')
        if nuid is not None and nuid.isdigit():
            self._rule[self.RULE_IND_NUID] = int(nuid)

    def is_matched(self, pinfo):
        if self._rule[self.RULE_IND_PID] > 0 and \
           self._rule[self.RULE_IND_PID] != pinfo.pid:
            return False
        if self._rule[self.RULE_IND_UID] > 0 and \
           self._rule[self.RULE_IND_UID] != pinfo.uid:
            return False
        if self._rule[self.RULE_IND_NUID] > 0 and \
           self._rule[self.RULE_IND_NUID] == pinfo.uid:
            return False
        if self._rule[self.RULE_IND_CMD] != '' and \
           re.match(self._rule[self.RULE_IND_CMD], pinfo.cmd) is None:
            return False
        return True

    def is_aggregated(self):
        return self._rule[self.RULE_IND_AGG]

    def get_displayname(self):
        return self._rule[self.RULE_IND_NAME]

class SubtreeMatcher:
    def __init__(self, config, _host):
        if 'processes' in config:
            self.parseRules(config['processes'])
        self.results = []
        self.modules = None
        self.host = _host

    def parseRules(self, rules):
        self.rules = []
        try:
            for rule_item in rules:
                new_rule = SubtreeMatcherRule()
                new_rule.set_rule(rule_item)
                self.rules.append(new_rule)
        except:
            sys.stderr.write("Parse rule configuration failed.")
            self.rules = []

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
            if rule.is_matched(pinfo):
                if rule.is_aggregated():
                    self.aggTree(pinfo, self.results[i])
                else:
                    self.results[i].add(self.getMetric(pinfo))

    def report(self, timestamp, reporter):
        for i in range(0, len(self.rules)):
            for j in range(0, len(self.modules)):
                module = self.modules[j]
                for k in range(0, module.size()):
                    name = "process.%s" % (module.naming()[k])
                    types = "proc=%s"%(self.rules[i].get_displayname())
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
                    name = "%s.%s"%(self.rules[i][self.RULE_IND_NAME],
                                    module.naming()[k])
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

class MapReduceMatcherRule:
    #rule definition:
    #pid, uid, cmdline, agg_sub_tree, nameschema

    RULE_LEN          = 8
    RULE_IND_PID      = 0
    RULE_IND_UID      = 1
    RULE_IND_CMD      = 2
    RULE_IND_AGG      = 3
    RULE_IND_NAME     = 4
    RULE_IND_NUID     = 5
    RULE_IND_NMAPPER  = 6
    RULE_IND_NREDUCER = 7
    RULEKEYTOID = { \
        'pid':RULE_IND_PID, 'uid':RULE_IND_UID,\
        'cmd':RULE_IND_CMD, 'agg':RULE_IND_AGG, \
        'name':RULE_IND_NAME, 'nuid':RULE_IND_NUID, \
        'nmapper':RULE_IND_NMAPPER, 'nreducer':RULE_IND_NREDUCER \
    }

    def __init__(self):
        self._rule = [0, 0, '', False, '', 0, 0, 0]

    def set_rule(self, conf):
        pid = safe_get(conf, 'pid')
        if pid is not None and pid.isdigit():
            self._rule[self.RULE_IND_PID] = int(pid)
        uid = safe_get(conf, 'uid')
        if uid is not None and uid.isdigit():
            self._rule[self.RULE_IND_UID] = int(uid)
        agg = safe_get(conf, 'aggregated')
        if agg is not None and (agg == 'True' or agg == 'False'):
            self._rule[self.RULE_IND_AGG] = bool(agg)
        name = safe_get(conf, 'displayname')
        if name is not None:
            self._rule[self.RULE_IND_NAME] = name
        nuid = safe_get(conf, 'nuid')
        if nuid is not None and nuid.isdigit():
            self._rule[self.RULE_IND_NUID] = int(nuid)
        nmapper = safe_get(conf, 'nmapper')
        if nmapper is not None and nmapper.isdigit():
            self._rule[self.RULE_IND_NMAPPER] = int(nmapper)
        nreducer = safe_get(conf, 'nreducer')
        if nreducer is not None and nreducer.isdigit():
            self._rule[self.RULE_IND_NREDUCER] = int(nreducer)

    def is_matched(self, pinfo):
        if self._rule[self.RULE_IND_PID] > 0 and \
           self._rule[self.RULE_IND_PID] != pinfo.pid:
            return False
        if self._rule[self.RULE_IND_UID] > 0 and \
           self._rule[self.RULE_IND_UID] != pinfo.uid:
            return False
        if self._rule[self.RULE_IND_NUID] > 0 and \
           self._rule[self.RULE_IND_NUID] == pinfo.uid:
            return False
        if self._rule[self.RULE_IND_CMD] != '' and \
           re.match(self._rule[self.RULE_IND_CMD], pinfo.cmd) is None:
            return False
        return True

    def get_num_mapper(self):
        return self._rule[self.RULE_IND_NMAPPER]

    def get_num_reducer(self):
        return self._rule[self.RULE_IND_NREDUCER]

    def get_displayname(self):
        return self._rule[self.RULE_IND_NAME]

class MapReduceMatcher(SubtreeMatcher):

    def __init__(self, config, _host):
        if 'mrtask' in config:
            self.parseRules(config['mrtask'])
        else:
            self.rules = []
        self.managers = []
        for i in range(len(self.rules)):
            self.managers.append(MRManager(
                self.rules[i].get_num_mapper(), 'm'))
            self.managers.append(MRManager(
                self.rules[i].get_num_reducer(), 'r'))
        self.host = _host

    def parseRules(self, rules):
        self.rules = []
        for rule_item in rules:
            new_rule = MapReduceMatcherRule()
            new_rule.set_rule(rule_item)
            self.rules.append(new_rule)

    def initMetric(self, modules):
        self.results = []
        self.modules = modules

    def startGroup(self):
        for manager in self.managers:
            manager.cleanUpdateList()

    def check(self, pinfo):
        for i in range(0, len(self.rules)):
            rule = self.rules[i]
            if rule.is_matched(pinfo):
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

def test():
    import config
    config_parser = config.ProcmonConfigParser()
    mrconf = config_parser.load_mrtask_config('../../etc/mrtask.xml')
    matcher = MapReduceMatcher(mrconf, "localhost")
    modules = [ProcInfoStat(), ProcInfoStatus(), ProcInfoIO()]
    matcher.initMetric(modules)
    plist = ProcMon()
    pid = 1
    proc = ProcInfo(pid, plist, modules)
    plist.procs[pid] = proc
    proc.update(10)
    proc.prepare_tree()
    proc.cmd = "4j12-1.4.3.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/commons-el-1.0.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/core-3.1.1.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/servlet-api-2.5-6.1.14.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/jetty-6.1.14.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/log4j-1.2.15.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/slf4j-api-1.4.3.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/xmlenc-0.52.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/jets3t-0.6.1.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/commons-cli-1.2.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/commons-httpclient-3.0.1.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/jasper-runtime-5.5.12.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/jetty-util-6.1.14.jar:/usr/local/sw/hadoop/build/ivy/lib/Hadoop/common/junit-3.8.1.jar::/l/b2/scratch/hadoop-data/global/mapred/local/taskTracker/jobcache/job_201106031747_0066/jars/classes:/l/b2/scratch/hadoop-data/global/mapred/local/taskTracker/jobcache/job_201106031747_0066/jars:/l/d2/scratch/hadoop-data/global/mapred/local/taskTracker/jobcache/job_201106031747_0066/attempt_201106031747_0066_r_000000_1/work -Dhadoop.log.dir=/l/a2/scratch/hadoop-data/global/log -Dhadoop.root.logger=INFO,TLA -Dhadoop.tasklog.taskid=attempt_201106031747_0066_r_000000_1 -Dhadoop.tasklog.totalLogFileSize=0 org.apache.hadoop.mapred.Child 127.0.0.1 44373 attempt_201106031747_0066_r_000000_1 -1985077290"
    matcher.startGroup()
    matcher.check(proc)
    matcher.endGroup()
    stdoutr = StdoutReporter()
    matcher.report(2, stdoutr)

def test2():
    import config
    config_parser = config.ProcmonConfigParser()
    procmonconf = config_parser.load_procmon_config('../../etc/procmon.xml')
    matcher = SubtreeMatcher(procmonconf, "localhost")
    modules = [ProcInfoStat(), ProcInfoStatus(), ProcInfoIO()]
    matcher.initMetric(modules)
    plist = ProcMon()
    pid = 1
    proc = ProcInfo(pid, plist, modules)
    plist.procs[pid] = proc
    proc.update(10)
    proc.prepare_tree()
    proc.cmd = 'pvfs2-client-core --child -a 5 -n -5 --logtype file'
    matcher.startGroup()
    matcher.check(proc)
    matcher.endGroup()
    stdoutr = StdoutReporter()
    matcher.report(2, stdoutr)

if __name__ == '__main__':
    test()
