#!/usr/bin/env python3

import re
import collections
import pickle as pkl
import math
import numpy as np

FREQ = 2417 # mhz
FSPL = 27.55 # this should be negative

_ap_log = 'ap.log'
_mac_re = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
_dbm_re = r'((?<=-)\d{2})'
_floor_plan = "plan.png"

def get_distance(dbm):
    log_freq = (20 * math.log10(FREQ)) 
    m = 10 ** ((FSPL  + dbm - log_freq) /20)
    return m
    
def gather_data():
    dataset = collections.defaultdict(lambda: [])

    with open(_ap_log, 'r') as fin:
        for line in fin:
            mac = re.search(_mac_re, line)
            dbm = re.search(_dbm_re, line)
            #print(mac.group(0), int(dbm.group(0)))
            splitted = line.split(' ')
            timestamp, name= splitted[0], splitted[5]
            timestamp = timestamp[1:-1]
            dbm = int(dbm.group(0))
            mac = mac.group(0)
            d = get_distance(dbm)
            dataset[mac].append((timestamp, dbm, d))

    with open('dataset.pkl', 'we') as fout:
        pkl.dump(dict(dataset), fout)
