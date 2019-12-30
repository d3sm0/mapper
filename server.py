#!/usr/bin/env python3

import struct
import socket
import threading
import traceback
import collections
import sys

from queue import Queue
from tol import get_center


host = '0.0.0.0'
port = 65432
n_requests = 5
something_pushed = threading.Condition()
rasp_connected = threading.Condition()

mac_info_queue = Queue()
all_known_macs = []
n_connected_rasp = 0

def client_thread(conn, addr, port, thread_id):
    PACKET_SIZE = 10 # 6 bytes MAC address + 4 bytes distance
    while True:
        msg = conn.recv(10, socket.MSG_WAITALL)
        print(msg)
        if (len(msg)) < 10:
            print("Client {} disconnected.".format(thread_id))
            all_known_macs[thread_id] = {}
            conn.close()
        fields = struct.unpack("<6Bi", msg)
        mac_addr = fields[0:6]
        distance = fields[6]

        print("Raspi {} sent data for mac {}, distance {}.".format(thread_id, mac_addr, distance))
        something_pushed.acquire()
        print("Pushing obtained data.")
        mac_info_queue.put((thread_id, mac_addr, distance))
        something_pushed.notify()
        something_pushed.release()

def compute_mac_addr_coordinates(raspi_mac_addrs):
    assert len(raspi_mac_addrs) == 2, 'Using {} mac addresses is unsupported.'.format(len(raspi_mac_addrs))
    center = get_center(raspi_mac_addrs[0], raspi_mac_addrs[1])
    return center.x, center.y

def render_mac_addr_coordinates(x, y, mac):
    print("Mac address {} found at {}!".format(mac, (x, y)))

def consume_mac_data():
    rasp_connected.acquire()
    while n_connected_rasp < 2:
        print("Waiting for raspberry to connect ({} connected)".format(n_connected_rasp))
        rasp_connected.wait()
    rasp_connected.release()
    print("All raspberries connected. Consuming data.")
    while True:
        something_pushed.acquire()
        while mac_info_queue.empty():
            something_pushed.wait()
        thread_id, mac_addr, distance = mac_info_queue.get()
        print("Received update from thread {} for mac address {}, distance {}".format(thread_id, mac_addr, distance))
        all_known_macs[thread_id][mac_addr] = distance
        available_for_this_mac = [mac_addr in all_known_macs[i] for i in range(len(all_known_macs))]
        if len(available_for_this_mac) >= 2:
            print("Data for mac address {} available!".format(mac_addr))
            x, y = compute_mac_addr_coordinates(available_for_this_mac)
            render_mac_addr_coordinates(x, y, mac_addr)
        something_pushed.release()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(n_requests)

    triangulator = threading.Thread(target=consume_mac_data).start()
    threads = []
    while True:
        print("Waiting for a connection.")
        conn, addr = s.accept()
        print(f"Connected with {addr[0]}:{addr[1]}")
        try:
            new_thread_id = len(all_known_macs)
            all_known_macs.append({})
            t = threading.Thread(target=client_thread, args=(conn,addr, port, new_thread_id)).start()
            threads.append(t)
            rasp_connected.acquire()
            n_connected_rasp += 1
            rasp_connected.notify()
            rasp_connected.release()
        except Exception as e:
            print("Failed to open connection")
            traceback.print_exc()

for t in threads:
    t.join()
