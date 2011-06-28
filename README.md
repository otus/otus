Otus
==========
Otus is a monitoring tool that attributes resource utilization to individual services in cluster.
It collects resource information (e.g. CPU usage, memory usage, and disk I/O) of processes of interest,
and visualize them. Especially, it supports many Hadoop services, for example, MapReduce, HDFS and HBase.
The tool is built atop of OpenTSDB (http://opentsdb.net/). The tool contains a plugin to OpenTSDB that collects resource information,
and provides a standalone web front-end to generate visual reports.

A snapshot of otus's web interface:

![screenshot!](https://github.com/otus/otus/raw/master/docs/otus.png)

Get started
===========
Otus depends on hbase and asynchbase for opentsdb,
uses Django and SQLlite for web front-end.

Get opentsdb running
--------------------
1 Get hbase-0.90.X - we've been using hbase-0.90.2

	# From http://hbase.apache.org/book/quickstart.html. Pick a mirror at http://www.apache.org/dyn/closer.cgi/hbase/ and run:
	curl -O http://link.to.mirror/.../hbase-0.90.X.tar.gz
	tar -xzvf hbase-0.90.X.tar.gz
	hbase-0.90.X/bin/start-hbase.sh

2 Get asyncbase

	git clone https://github.com/stumbleupon/asynchbase.git
	cd asynchbase
	git checkout d1aff70c71d3
	make
	cd ..

3 Get and run OpenTSDB locally

	# From http://opentsdb.net/getting-started.html
	git clone git://github.com/stumbleupon/opentsdb.git
	cd opentsdb
	make || make MD5=md5sum
	make staticroot
	cp ../asynchbase/build/hbaseasync-1.0.jar ./third_party/hbase/hbaseasync-1.0.jar
	env COMPRESSION=none HBASE_HOME=../hbase-0.90.X ./src/create_table.sh
	./src/tsdb mkmetric http.hits sockets.simultaneous lolcats.viewed
	./src/tsdb tsd --port=4242 --staticroot=build/staticroot --cachedir=/tmp/tsd

4 Create new metrics for Otus in OpenTSDB
	
		

Get otus running
----------------------
1 Get otus:

	git git://github.com/otus/otus.git

2 Install tcollector with otus plugin
	
	otus plugin contains serveral files:
	otus/tcollector/collectors/0/procstat.py
	otus/tcollector/collectors/etc/mrtask.conf
	otus/tcollector/collectors/etc/procmon.conf
	otus/tcollector/collectors/lib/procmon

  Configure otus plugin:
  In procmon.conf, it specifies what long running processes should be monitored.
  It contains multiple lines, each line specifies a property of a particular process.
  The otus plugin will collect the pid (process ID), uid (user ID) 
  and cmd (command line) of each process, and check whether
  pid, uid, cmd is matched with the properties specified in procmon.conf.

  The line format is 
      [pid PID_PROCESS] [uid UID_PROCESS] [npid PID_PROCESS] [nuid UID_PROCESS] cmd RE_PROCESS_COMMAND name PROCESS_NAME
  
      		pid PID_PROCESS: it specifies the process ID of monitored process is PID_PROCESS
	  	npid PID_PROCESS: it specifies the process ID of monitored process is not PID_PROCESS
  		uid PID_PROCESS: it specifies the user ID of monitored process is UID_PROCESS
  		nuid PID_PROCESS: it specifies the user ID of monitored process is not UID_PROCESS
  		cmd RE_PROCESS_COMMAND: it specifies the command line (in /proc/pid/cmdline) is matched with the regular expression: RE_PROCESS_COMMAND
  		name PROCESS_NAME: it specifies the name that be finally shown in visual reports to identify the process. (e.g, the metric "TaskTracker's memory" will be recored as "process.vmrss proc=TaskTracker" in OpenTSDB).
  

  In mrjob.conf, it specifies what Map-Reduce task processes should be monitored:
  The property format is:
	
  	[pid PID_PROCESS] [uid UID_PROCESS] nmapper NUMBER_OF_MAPPER_TASKS nreducer NUMBER_OF_REDUCER_TASKS

  pid and uid have the same meaning as the above.

  	nmapper NUMBER_OF_MAPPER_TASKS: it specifies the maximum number of mapper tasks running in each node (a parameter of Hadoop MapReduce system)
	nreducer NUMBER_OF_REDUCER_TASKS: it specifies the maximum number of reducer tasks running in each node (a parameter of Hadoop MapReduce system)

3 Install otus web front-end:
  Otus web front-end is built by using Django web framework.

  Install Django web framework: https://docs.djangoproject.com/en/dev/intro/install/
  Install SQLLite: http://www.sqlite.org/download.html
  Quick install in debian/ubuntu:
	
	sudo apt-get install python-django
	sudo apt-get install sqlite

  Configure otus web front-end, edit the file in otus/webui/media/lib/tsd/configuration.js
 	
	OpenTSDBURL: the server address of OpenTSDB where otus can get data from 
	NumMapper: the number of mapper tasks
	NumReducer: the number of reducer tasks
	ServerList: a list of host names that are monitored by tcollector 


2. Features that are coming soon:
(a) JMX plugin for OpenTSDB to collect internal statistics of Hadoop software

(b) Vistual Reports about internal statistics of Hadoop software
