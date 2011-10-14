#!/usr/bin/env python
"""import various /proc stats from /proc into TSDB"""

import os 
import sys
MAINPATH=os.path.dirname(os.path.abspath(__file__))+"/../"
sys.path.append(MAINPATH+'lib/stat')
import time
import dfstat
import ifstat
import netstat
import iostat
import procstats

def init(plugins):
    min_interval = 1000
    for plugin in plugins:
        if plugin[1] < min_interval:
           min_interval = plugin[1]
    return min_interval

def main():
    plugins = [
        [0, dfstat.COLLECTION_INTERVAL, dfstat.main],
        [0, ifstat.COLLECTION_INTERVAL, ifstat.main],
        [0, netstat.COLLECTION_INTERVAL, netstat.main],
        [0, iostat.COLLECTION_INTERVAL, iostat.main],
        [0, procstats.COLLECTION_INTERVAL, procstats.main]
    ]
    min_interval = init(plugins)

    for plugin in plugins:
        plugin[2]()

    while True:
        for plugin in plugins:
            if plugin[0] >= plugin[1]:
                plugin[2]()
                plugin[0] = 0
            else:
                plugin[0] += min_interval
        time.sleep(min_interval)

if __name__ == "__main__":
    main()

