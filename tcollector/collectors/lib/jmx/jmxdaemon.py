#!/usr/bin/env python
import os
import sys
import time
import signal
import subprocess

class JMXClient:
  def __init__(self, cmdJMX):
    self._cmdJMX = cmdJMX

  def execute(self, param_list):
    try:
      p = subprocess.Popen(param_list, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      result = p.stdout.readlines()
      p.stdout.close()
      if len(result) > 0 and result[0].find("Exception in thread")>=0:
        return (-1, [])
      else:
        return (0, result)
    except Exception, e:
      print time.strftime('%X %x %Z')+': An exception raises in collectData(): '+str(e)
      os.kill(p.pid, signal.SIGTERM)
      return (-1, [])

  def collect(self, host, port, beanName, metric):
    param_list = ['java', '-Xmx64m', '-jar', self._cmdJMX, '-', host+':'+port, beanName]
    param_list.extend(metric)
    (flag, result) = self.execute(param_list)
    return (flag, result)

class MetricBean:
  def __init__(self, _host, _port, _beanName, _prefix, _metricList):
    self.host = _host
    self.port = _port
    self.prefix = _prefix
    self.beanName = _beanName
    self.metricList = _metricList;
    self.oldval = [0] * len(_metricList)
    self.newval = [0] * len(_metricList)

  def collectOne(self, jmxclient, metric):
    return jmxclient.collect(self.host, self.port, self.beanName, [metric])

  def collectAll(self, jmxclient):
    i = 0
    try:
      if len(self.metricList) == 0:
        return
      (flag, result) = jmxclient.collect(self.host, self.port, self.beanName, self.metricList)
      if flag == 0 and len(result) == len(self.metricList):
        for i in range(0, len(result)):
          self.oldval[i] = 0
          self.newval[i] = float(result[i].split()[-1])
    except:
      pass

  def check(self, jmxclient):
    newMetricList = []
    for metric in self.metricList:
      (flag, result) = self.collectOne(jmxclient, metric)
      if flag == 0:
        try:
          float(result[0].split()[-1])
          newMetricList.append(metric)
        except ValueError:
          pass
      else:
        print "remove: "+metric
    self.metricList = newMetricList
    self.oldval = [0] * len(newMetricList)
    self.newval = [0] * len(newMetricList)

  def report(self, reporter):
    avgFilesPerTablet = -1;
    numTablets = -1;
    nowtime = time.time()
    for i in range(0, len(self.metricList)):
      reporter.report(self.prefix+"."+self.metricList[i], int(nowtime), self.newval[i])
      if (self.metricList[i] == "AverageFilesPerTablet"):
        avgFilesPerTablet = self.newval[i]
      if (self.metricList[i] == "OnlineCount"):
        numTablets = self.newval[i]
    if numTablets != -1:
      reporter.report(self.prefix+".TotalMapFiles", int(nowtime), int(numTablets*avgFilesPerTablet));

class JMXDaemon:
  def __init__(self, _reporter, attr):
    self.jmxclient = JMXClient(attr.get("jmxcmd", "jmxclient.jar"))
    self.reporter = _reporter
    self.beanList = []

  def config(self, attr):
    host = attr.get("hostname", "localhost")
    servertype = attr.get("servertype", "HBase.RegionServer")
    if servertype == 'HBase.Master':
      self.addBean(MetricBean(host, '10101', 'hadoop:name=MasterStatistics,service=Master', 'hbase.Master',\
	 ['cluster_requests', 'splitTimeNumOps', 'splitTimeAvgTime','splitTimeMinTime','splitTimeMaxTime',\
	  'splitSizeNumOps', 'splitSizeAvgTime', 'splitSizeMinTime', 'splitSizeMaxTime', 'cluster_requests',]))
    elif servertype == 'HBase.RegionServer': 
      self.addBean(MetricBean(host, '10102', 'hadoop:name=RegionServerStatistics,service=RegionServer', 'hbase.RegionServer', \
         ['blockCacheFree','memstoreSizeMB','regions','blockCacheCount','blockCacheMissCount','blockCacheHitRatio','blockCacheHitCount',\
          'storefiles','blockCacheEvictedCount','storefileIndexSizeMB','stores','compactionQueueSize',\
          'compactionTimeNumOps','blockCacheSize','requests']))
    elif servertype == 'Accumulo.TabletServer':
      self.addBean(MetricBean(host, '8010', 'cloudbase.server.metrics:instance=tserver,name=TabletServerMBean,service=TServerInfo',\
         'Accumulo.TabletServer', ['Entries','Ingest','MajorCompactions',\
          'MinorCompactions','MinorCompactionsQueued','OnlineCount','OpeningCount','Queries',\
          'UnopenedCount','TotalMinorCompactions','AverageFilesPerTablet']))

  def addBean(self, bean):
    self.beanList.append(bean)

  def scan(self):
    for bean in self.beanList:
      bean.collectAll(self.jmxclient)
      bean.report(self.reporter)
