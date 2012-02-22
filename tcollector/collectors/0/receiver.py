#!/usr/bin/env python
import os
import sys
import threading
import time
import SocketServer
import Queue
MAINPATH=os.path.dirname(os.path.abspath(__file__))+"/../"

class MessageUDPHandler(SocketServer.BaseRequestHandler):
    """Handle requests from clients, and put them into message queue """
    msg_queue = None

    def handle(self):
        data = self.request[0].strip()
        MessageUDPHandler.msg_queue.put(data)


class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


def get_with_default(conf, key, default):
    if key in conf:
        return conf[key]
    else:
        return default


def init(conf):
    try:
        f = open(MAINPATH+"etc/reciever.conf", "r")
        for l in f:
            pos = l.find(' ')
            conf[l[0:pos]] = l[pos+1:]
        f.close()
    except:
        conf = {}


def main():
    conf = {}
    init(conf)
    interval = get_with_default(conf, 'interval', 10)
    host = get_with_default(conf, 'hostname', 'localhost')
    port = get_with_default(conf, 'port', 10600)
    msg_queue = Queue.Queue()
    MessageUDPHandler.msg_queue = msg_queue
    server = SocketServer.UDPServer((host, port), MessageUDPHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.setDaemon(True)
    server_thread.start()

    while True:
        time.sleep(interval)
        for i in range(msg_queue.qsize()):
            try:
                item = msg_queue.get()
                print item
            except Queue.Empty as e:
                break
        sys.stdout.flush()

if __name__ == "__main__":
  main()
