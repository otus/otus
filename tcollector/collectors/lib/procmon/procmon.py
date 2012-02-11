#!/usr/bin/python
import os, sys, getopt
import time
import socket
from constant import *
from metriclist import *
from procinfo import *
from reporter import *
from matcher import *

class ProcInfo:
    def __init__(self, pid, plist, modules):
        self.pid = pid
        self.plist = plist
        self.oldtime = 0
        self.modules = modules
        self.met = MetricList(modules, 0)
        self.getIDs()

    def getIDs(self):
        self.cmd = getCmdLine(self.pid)
        (self.ppid, self.uid) = getPPidAndUid(self.pid)

    def update(self, nowtime):
        interval = 10
        if nowtime - self.oldtime > interval * 2:
            self.getIDs()
        for i in range(0, len(self.modules)):
            self.modules[i].update(self.pid, \
                self.met.getRow(i), nowtime-self.oldtime)
        self.oldtime = nowtime

    def prepare_tree(self):
        self.child = []

    def create_tree(self):
        if self.ppid in self.plist.procs:
            self.parent = self.plist.procs[self.ppid]
            self.parent.child.append(self.pid)
        else:
            self.parent = None

    def get_subtree(self):
        queue = [self.pid]
        tree = set([])    #Prevent there is a cycle
        tree.add(self.pid)
        head = 0
        while head < len(tree):
            v = queue[head]
            head += 1
            if v in self.plist.procs:
                p = self.plist.procs[v]
            else:
                continue
            for ch in p.child:
                if ch not in tree:
                    tree.add(ch)
                    queue.append(ch)
        return tree

    def getAggTreeMetric(self):
        tree = self.get_subtree()
        met = MetricList(self.modules, 0)
        for pid in tree:
            met.add(self.plist.procs[pid].getMetric())
        return met

    def queryMetric(self, x, y):
        return self.met[x][y]

    def getMetric(self):
        return self.met


class ProcMon:
    def __init__(self):
        self.procs = {}
        self.modules = []
        self.reporters = []
        self.matchers = []
        self.active = []

    def register_module(self, module):
        self.modules.append(module)

    def register_reporter(self, reporter):
        self.reporters.append(reporter)

    def register_matcher(self, matcher):
        self.matchers.append(matcher)

    def initialize(self):
        for matcher in self.matchers:
            matcher.initMetric(self.modules)

    def update(self):
        self.active = []
        for f in os.listdir(PATH.PROC):
            if len(f) > 0 and f.isdigit():
                pid = int(f)
                self.active.append(pid)
                if pid not in self.procs:
                    self.procs[pid] = ProcInfo(pid, self, self.modules)
                self.procs[pid].update(int(time.time()))

    def startGroup(self):
        for reporter in self.reporters:
            reporter.startGroup()
        for matcher in self.matchers:
            matcher.startGroup()

    def monitor(self):
        self.update()
        for pid in self.active:
            pinfo = self.procs[pid]
            pinfo.prepare_tree()
        for pid in self.active:
            pinfo = self.procs[pid]
            pinfo.create_tree()
        for pid in self.active:
            pinfo = self.procs[pid]
            for matcher in self.matchers:
                matcher.check(pinfo)

    def report(self):
        for matcher in self.matchers:
            for reporter in self.reporters:
                matcher.report(int(time.time()), reporter)

    def run(self, interval):
        while (1):
            self.startGroup()
            self.monitor()
            for matcher in self.matchers:
                matcher.endGroup()
            self.report()
            for reporter in self.reporters:
                reporter.endGroup()
            time.sleep(interval)

if __name__ == "__main__":
    main()
