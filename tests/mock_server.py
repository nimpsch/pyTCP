import select
import socketserver
import threading
from queue import Queue


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    allow_reuse_address = True

    def handle(self):
        ready_read, ready_write, exceptional = select.select([self.request], [], [self.request], 1)

        for sock in ready_read:
            recv_msg = sock.recv(4048)
            sock.send(recv_msg)
            self.server.queue.add(recv_msg)


class MockServer:
    socketserver.TCPServer.allow_reuse_address = True

    def __init__(self, ip, port):
        self.server = ThreadedTCPServer((ip, port), ThreadedTCPRequestHandler)
        self.server.queue = self
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server.socket.setblocking(False)

        self.messages = Queue(maxsize=1)

    def start_server(self):
        self.server_thread.start()

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()

    def add(self, message):
        if not self.messages.full():
            self.messages.put(message)

    def get_message(self):
        return self.messages.get()
