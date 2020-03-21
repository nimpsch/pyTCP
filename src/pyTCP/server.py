import select
import socketserver
import threading
from queue import Queue


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        while self.server.instance.keep_alive:
            ready_read, ready_write, exceptional = select.select([self.request], [], [], 1)

            for sock in ready_read:
                if sock == self.request:
                    recv_msg = sock.recv(self.server.instance.receive_bytes)
                    if recv_msg is not None:
                        self.request.sendall(recv_msg)
                        self.server.instance.add(recv_msg)


class EchoServer:
    socketserver.TCPServer.allow_reuse_address = True

    def __init__(self, ip, port, receive_bytes=4096):
        self.server = ThreadedTCPServer((ip, port), ThreadedTCPRequestHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server.socket.setblocking(False)
        self.server.instance = self
        self.keep_alive = False
        self.receive_bytes = receive_bytes
        self._last_received = Queue(maxsize=1)

    @property
    def last_received(self):
        return self._last_received.get()

    def start_server(self):
        self.keep_alive = True
        self.server_thread.start()

    def stop_server(self):
        self.keep_alive = False
        self.server.shutdown()
        self.server.server_close()

    def add(self, message):
        if not self._last_received.full():
            self._last_received.put(message)
        else:
            self._last_received.get_nowait()
            self._last_received.put(message)
