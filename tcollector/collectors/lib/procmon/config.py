#!/usr/bin/python
#########################################################################
# Author: Kai Ren
# Created Time: 2012-02-10 17:14:28
# File Name: ./config.py
# Description:
#########################################################################

import match
import xml.etree.ElementTree as elmtree

class ProcmonConfigParser:
    def load_config(self, config_filename):
        try:
            tree = elmtree.parse(config_filename)
            rootElement = tree.getroot()
            config = {}
            if rootElment.tag == 'configuration':
                proc_group = rootElment.findall('processes')
                proc_list = []
                for procs in proc_group:
                    for proc_elem in procs.findall('process'):

                config['processes'] = proc_list

            return config
        except:
            return []  #empty config

