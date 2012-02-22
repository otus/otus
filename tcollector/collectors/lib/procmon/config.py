#!/usr/bin/python
#########################################################################
# Author: Kai Ren
# Created Time: 2012-02-10 17:14:28
# File Name: ./config.py
# Description:
#########################################################################

import xml.etree.ElementTree as elmtree

class ProcmonConfigParser:
    def load_procmon_config(self, config_filename):
        try:
            tree = elmtree.parse(config_filename)
            rootElement = tree.getroot()
            config = {}
            if rootElement.tag == 'configuration':
                proc_group = rootElement.findall('processes')
                proc_list = []
                for procs in proc_group:
                    for proc_elem in procs.findall('process'):
                        proc_prop = {}
                        for prop in list(proc_elem):
                            proc_prop[prop.tag] = prop.text
                        proc_list.append(proc_prop)
                config['processes'] = proc_list
            return config
        except:
            return {} #empty config

    def load_mrtask_config(self, config_filename):
        try:
            tree = elmtree.parse(config_filename)
            rootElement = tree.getroot()
            config = {}
            if rootElement.tag == 'configuration':
                mrtask_config = []
                mrtask_prop = {}
                mrtask = rootElement.find('mrtask')
                for prop in list(mrtask):
                    mrtask_prop[prop.tag] = prop.text
                mrtask_config.append(mrtask_prop)
                config['mrtask'] = mrtask_config
            return config
        except:
            return {}  #empty config

if __name__ == '__main__':
    config_parser = ProcmonConfigParser()
    print config_parser.load_procmon_config('../../etc/procmon.xml')
    print config_parser.load_mrtask_config('../../etc/mrtask.xml')
