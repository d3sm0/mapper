import socket
import time

host = '10.0.0.1'
port = 65432
buffer_size = 1024

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

    try:
        s.connect((host, port))
        print("Connected with server {}:{}".format(host, ip)
    except Exception as e:
        print("Connection error")

    while True:
        s.send(b'clientA: Hello, World')
        data = s.recv(buffer_size)
        print('rec', data.decode())
        time.sleep(5)
