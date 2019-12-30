#!/usr/bin/env python3

import math
import re
import socket
import struct
import time
import subprocess
import sys

FREQ = 2417 # mhz
FSPL = 27.55 # this should be negative

_mac_re = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
_dbm_re = r'((?<=-)\d{2})'
_floor_plan = "plan.png"

def get_distance(dbm):
    log_freq = (20 * math.log10(FREQ)) 
    m = 10 ** ((FSPL  + dbm - log_freq) /20)
    return m
    
host = sys.argv[1]
port = 65432
buffer_size = 1024

_capture_ap = ['sudo','bettercap','-no-colors', '-iface', 'mon0', '-caplet', 'ap.cap']

p = subprocess.Popen(_capture_ap, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
print(p.stdout)

def parse_output_line(line):
    print("Line: {}".format(line))
    mac = re.search(_mac_re, line)
    if mac is None:
        return None
    dbm = re.search(_dbm_re, line)
    assert(dbm != None)
    #print(mac.group(0), int(dbm.group(0)))
    splitted = line.split(' ')
    timestamp, name= splitted[0], splitted[5]
    timestamp = timestamp[1:-1]
    dbm = int(dbm.group(0))
    mac = bytes([int(b, 16) for b in mac.group(0).split(':')])
    assert(len(mac) == 6)
    d = get_distance(dbm)
    return (d, dbm, mac, timestamp)

def parse_program_output(s, out_file):
    while True:
        for line in p.stdout:
            parsed_output = parse_output_line(line.decode())
            if parsed_output is None:
                continue
            d, dbm, mac, timestamp = parsed_output
            #s.send(b'clientA: Hello, World')
            #data = s.recv(buffer_size)
            print('Rec {}'.format(line))
            print('MAC {} -> d {}'.format(mac, d))
            out_file.write(line)
            try:
                s.send(struct.pack("<6Bf", *mac, d))
            except:
                print("Connection closed.")
                s.close()
                break
        #time.sleep(5)

with open('dump.txt', 'wb') as out_file:
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((host, port))
                print("Connected with server {}:{}".format(host, port))
                parse_program_output(s, out_file)
            except Exception as e:
                print("Connection error")
                time.sleep(1)

