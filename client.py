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

# host = '192.168.1.62' # sys.argv[1]
host = "F8:94:C2:6B:C3:AC"
#host = ''
port = 1
buffer_size = 1024

important_clients = {"F8:94:C2:6B:C3:A8":"main_room","1C:15:1F:39:99:29":"phone"}

_capture_ap = ['sudo','bettercap','-no-colors', '-iface', 'mon0', '-caplet', 'ap.cap']

p = subprocess.Popen(_capture_ap, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
print(p.stdout)

get_address = lambda mac: bytes([int(b, 16) for b in mac.split(':')])
important_clients = {get_address(k):v for k,v in important_clients.items()}

def parse_output_line(line):
    print("Line: {}".format(line))
    mac = re.search(_mac_re, line)
    if mac is None:
        print(f"couldn't find mac for line {line}")
        return None
    dbm = re.search(_dbm_re, line)
    if dbm is None:
        print(f"couldn't compute dbm for line {line}")
        return None
    #print(mac.group(0), int(dbm.group(0)))
    splitted = line.split(' ')
    timestamp, name= splitted[0], splitted[5]
    timestamp = timestamp[1:-1]
    dbm = int(dbm.group(0))
    mac = get_address(mac.group(0))
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
            out_file.write(line)
            try:
                if mac in important_clients.keys():
                    print('Rec {}'.format(line.strip()))
                    print('MAC {} -> d {:.2f}'.format(mac, d))
                    s.send(struct.pack("<6Bf", *mac, d))
            except:
                print("Connection closed.")
                s.close()
                return
        #time.sleep(5)

import bluetooth
from contextlib import contextmanager

@contextmanager
def ble_socket(*args,**kwargs):
    s = bluetooth.BluetoothSocket(*args,**kwargs)
    try:
        yield s
    finally:
        s.close()


with open('dump.txt', 'wb') as out_file:
    while True:
        #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        with ble_socket(bluetooth.RFCOMM) as s:
            try:
                s.connect((host, port))
                print("Connected with server {}:{}".format(host, port))
                parse_program_output(s, out_file)
            except Exception as e:
                print("Connection error: {}".format(e))
                time.sleep(1)
                raise e

