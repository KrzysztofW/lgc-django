#!/usr/bin/python3

import socket
import threading
from struct import pack

MAX_FILE_SIZE=8192
DEF_PORT=14376

class TcpClient:
    def sock_connect(self, hosts, port=DEF_PORT):
        for host in hosts:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(5)
                self.sock.connect((host, port))
                return
            except:
                print("connection to", host, "has failed")
                self.sock.close()

    def sock_send(self, msg):
        totalsent = 0
        msg = msg.encode()

        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def sock_receive(self):
        chunk = self.sock.recv(MAX_FILE_SIZE)
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        return chunk

    def sock_close(self):
        self.sock.close()

class TcpServer:
    workers = []
    allowed_hosts = []

    def __init__(self, cb, host, port=DEF_PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (host, port)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(server_address)
        self.sock.listen(1)
        self.cb = cb

    def allow_from(self, hosts):
        self.allowed_hosts = hosts

    def sock_receive(self, conn):
        return conn.recv(MAX_FILE_SIZE)

    def worker(self, conn, client_addr):
        try:
            while True:
                data = conn.recv(MAX_FILE_SIZE).decode()
                #print('received "%s"' % data)
                if data:
                    res = self.cb(data)
                    if res:
                        print("sending ret:%s" % str(res))
                        conn.sendall(str(res).encode())
                else:
                    #print('no more data from', client_addr)
                    break
        finally:
            conn.close()

    def sock_accept(self, conn, client_addr):
        t = threading.Thread(target=self.worker, args=(conn, client_addr))
        self.workers.append(t)
        t.start()

    def run(self):
        #print('waiting for a connection')
        conn, client_addr = self.sock.accept()
        #print('connection from', client_addr)
        if client_addr[0] not in self.allowed_hosts:
            print('%s not allowed'%client_addr[0])
            conn.close()
            return
        self.sock_accept(conn, client_addr)
