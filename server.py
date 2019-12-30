import socket
import threading
import traceback
import collections
import sys

from Queue import Queue
from tol import get_center


host = '10.0.0.1'
port = 65432
n_requests = 5

def check_size(data, max_buffer_size=1024):
    data_size = sys.getsizeof(data)
    if data_size > max_buffer_size:
            print(f"The input size is greater than expected {data_size}")


def client_thread(conn, addr, port, storage,buffer_size=1024):
    while True:
        msg = conn.recv(buffer_size).decode('utf-8').rstrip()
        # handle msg
        print(msg)
        
        try:
            conn.send('-'.encode('utf-8'))
        except Exception as e:
            print("Client down")
            conn.close()
            break


storage = collections.defaultdict(lambda: Queue(queue_size))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(n_requests)

    threads = []
    while True:
        conn, addr = s.accept()
        print(f"Connected with {addr[0]}:{addr[1]}")
        try:
            t = threading.Thread(target=client_thread, args=(conn,addr, port, storage)).start()
            threads.append(t)
        except Exception as e:
            print("Failed to open connection")
            traceback.print_exc()

for t in threads:
    t.join()
