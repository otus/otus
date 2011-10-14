from HTMLParser import HTMLParser
import urllib
import os, sys, time, string, getopt, re

class Table():
  def __init__(self, name):
    self._table = []
    self._row = []
    self._name = name

  def endrow(self):
    self._table.append(self._row)
    self._row = []

  def append(self, elm):
    elm.replace('\t', '_')
    self._row.append(elm)

  def get(self):
    return self._table

  def dump(self, report):
    for row in self._table:
      rowstr = ""
      for elm in row:
        rowstr += str(elm) + " "

class HTMLTableParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)

  def reset(self):
    HTMLParser.reset(self)
    self._elemStack = []
    self._nextUrls = []
    self._tables = []
    self._table_id = ""
    self._table = None
    self._cell = ""
    self._intable = False
    self._inrow = False
    self._incell = False

  def newtable(self, name):
    self._table = Table(name)

  def handle_data(self, data):
    if self._intable and self._inrow and self._incell:
      if data != '\n':
        self._cell += data

  def handle_starttag(self, tag, attrs):
    self._elemStack.append(tag)
    id = ''
    if tag == 'table':
      self._intable = True
      self.newtable(id)
    if self._intable:
      if tag == 'tr':
        self._inrow = True
      if self._inrow and (tag == 'td' or tag == 'th'):
        self._incell = True

  def handle_endtag(self, tag):
    if self._intable:
      if tag == 'tr':
        self._table.endrow()
        self._inrow = False
      if self._incell and (tag == 'td' or tag == 'th'):
        self._table.append(self._cell)
        self._cell = ""
        self._incell = False
    if tag == 'table':
      self._intable = False
      if self._table is not None:
        self._tables.append(self._table)

  def getNextUrls(self):
    return self._nextUrls

  def getTables(self):
    return self._tables

class CrawlDaemon:
  def __init__(self, _reporter):
    self.urlList = []
    self.nameList = []
    self.parser = HTMLTableParser()
    self.reporter = _reporter
    self.lastTime = 0

  def dumpUrl(self, url):
    try:
      f = urllib.urlopen(url)
      lines = f.readlines()
      f.close()
    except:
      return []
    return lines

  def initTabletServers(self):
    self.addUrl("ICT.Master", "http://localhost:50095/tables")
    lines = self.dumpUrl("http://localhost:50095/tservers")
    for l in lines:
      patt = "/tservers?s="
      pos = l.find(patt)
      if pos >= 0:
        npos = l.find("'>", pos)
        host = "cloud%d"%(int(l[pos+len(patt)+7:npos-6])-1)
        self.addUrl(host, "http://localhost:50095"+l[pos:npos])

  def addUrl(self, name, url):
    self.nameList.append(name)
    self.urlList.append(url)

  def dumpTables(self, url):
    lines = self.dumpUrl(url)
    self.parser.reset()
    for line in lines:
      self.parser.feed(line)
    self.parser.close()
    return self.parser.getTables()

  def getValue(self, num):
    num = num.replace(',','')
    try:
      if num[-1] == 'G':
        ans = float(num[0:-1]) * 1000000000
      elif num[-1] == 'M':
        ans = float(num[0:-1]) * 1000000
      elif num[-1] == 'K':
        ans = float(num[0:-1]) * 1000
      elif num[-1] == ')':
        p = num.find('(')
        ans = float(num[0:p])
      else:
        ans = float(num)
    except ValueError, e:
      ans = 0
    return ans

  def dumpMaster(self, timestamp, name, url):
    tables = self.dumpTables(url)
    if (len(tables) == 0):
      return
    table = tables[0].get()
    tot = [0] * len(table[0])
    for i in range(1, len(table)):
      for j in range(2, len(table[i])):
        num = table[i][j];
        tot[j] += self.getValue(num)
    for j in range(2, len(table[i])):
      mname = table[0][j]
      if mname[0] == '#':
        mname = "Num"+mname[1:]
      self.reporter.report(name+'.'+mname, timestamp, str(tot[j]))

  def dumpTablet(self, timestamp, name, url):
    tables = self.dumpTables(url)
    table = tables[1].get()
    for i in range(1, len(table)):
      self.reporter.reportLogger("ICT.Tablet.Total"+table[i][0], timestamp, self.getValue(table[i][1]), "host=%s"%(name))

  def scan(self, interval):
    now = int(time.time())
    self.dumpMaster(now, self.nameList[0], self.urlList[0])
    if now - self.lastTime > interval * 3:
      for i in range(1, len(self.urlList)):
        self.dumpTablet(now, self.nameList[i], self.urlList[i])
      self.lastTime = now
