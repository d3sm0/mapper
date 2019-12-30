#!/usr/bin/env python3

import numpy
import scipy
import scipy.optimize
import struct
import socket
import threading
import traceback
import collections
import sys
import numpy as np

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

def measure_distance_error(supposed_location, sniffer_locations, sniffer_distances):
    err = 0
    for loc, dist in zip(sniffer_locations, sniffer_distances):
        actual_dist = numpy.linalg.norm(supposed_location - loc)
        dist_err = actual_dist - dist
        err += dist_err * dist_err
    print("Location {} -> err {}".format(supposed_location, err))
    return err


def find_location(ap_data):
    """
    @param ap_data list of couples (sniffer location [x,y], distance to sniffer)
    """
    sniffer_locations = np.array([loc for loc, _ in ap_data])
    sniffer_distances = np.array([dist for _, dist in ap_data])
    start_point = np.mean(sniffer_locations, axis=0)
    print("Location mean of known sniffers: {}".format(start_point))
    result = scipy.optimize.minimize(measure_distance_error, start_point, (sniffer_locations, sniffer_distances))
    return result


def client_thread(conn, addr, port, thread_id):
    PACKET_SIZE = 10 # 6 bytes MAC address + 4 bytes distance
    while True:
        msg = conn.recv(10, socket.MSG_WAITALL)
        print(msg)
        if (len(msg)) < 10:
            print("Client {} disconnected.".format(thread_id))
            all_known_macs[thread_id] = {}
            conn.close()
        fields = struct.unpack("<6Bf", msg)
        mac_addr = fields[0:6]
        distance = fields[6]

        print("Raspi {} sent data for mac {}, distance {}.".format(thread_id, mac_addr, distance))
        something_pushed.acquire()
        print("Pushing obtained data.")
        mac_info_queue.put((thread_id, mac_addr, distance))
        something_pushed.notify()
        something_pushed.release()

raspi0_location = [0,0]
raspi1_location = [0.6, 0.8]

def compute_mac_addr_coordinates(raspi_mac_addrs):
    assert len(raspi_mac_addrs) == 2, 'Using {} mac addresses is unsupported.'.format(len(raspi_mac_addrs))
    #center = get_center(raspi_mac_addrs[0], raspi_mac_addrs[1])
    center = find_location([(raspi0_location, raspi_mac_addrs[0]), (raspi1_location, raspi_mac_addrs[1])])
    if center.success:
        print("Raspi distances: {} -> point is at {}".format(raspi_mac_addrs, center.x))
    return center

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
        # Pick all raspberries that know about this mac address
        available_for_this_mac = {thread_id: all_known_macs[thread_id][mac_addr] for thread_id in range(len(all_known_macs)) if mac_addr in all_known_macs[thread_id]}
        if len(available_for_this_mac) >= 2:
            print("Data for mac address {} available!".format(mac_addr))
            result = compute_mac_addr_coordinates([available_for_this_mac[0], available_for_this_mac[1]])
            if result.success:
                x, y = result.x
                render_mac_addr_coordinates(x, y, mac_addr)
            else:
                print("Couldn't compute center :(")
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
        print("Connected with {}:{}".format(addr[0],addr[1]))
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
