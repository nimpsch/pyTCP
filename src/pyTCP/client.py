import logging
import socket
import time

from .client_errors import ClientTimeoutError


class TcpClient:
    """A tcp client

    Attributes
    ----------
    host : str
        The ip address of the tcp server.
    port : int
        The port of the tcp server.
    auto_reconnect : bool
        If true, a reconnect will be made on connection loss.
    logger : :obj:
        An instance of the logging module.
    buffer : bool, default=True
        The split part of the msg which was not returned.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8080, auto_reconnect: bool = True):
        """The constructor.

        Parameters
        ----------
        host : str, default="127.0.0.1"
            The ip address of the tcp server.
        port : int, default=8080
            The port of the tcp server.
        auto_reconnect : bool, default=True
            If true, a reconnect will be made on connection loss.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self._connected = False
        self.auto_reconnect = auto_reconnect

        self.logger = logging.getLogger(__name__)
        self.buffer = []

    @property
    def is_connected(self):
        """bool: Returns True if connected."""
        return self._connected

    def connect(self, timeout: float = 10.0):
        """ Tries to connect to the given host. Waits 0.5 seconds until another try will be made.

        Parameters
        ----------
        timeout : float, default 10.0
            The maximum time this function will try to connect until a ClientTimeoutError is raised.

        Raises
        ------
        ClientTimeoutError
            If no connection could be established in the given time a ClientTimeoutError is raised.
        """
        timeout_start = time.time()
        while not self._connected and time.time() < timeout_start + timeout:
            try:
                self.sock.connect((self.host, self.port))
                self._connected = True
                return
            except socket.error:
                self.logger.error("error creating a connection, trying again ... ")
                time.sleep(0.5)
                continue
        raise ClientTimeoutError("timeout while connecting")

    def send(self, data: bytes):
        """ Send a message to the socket. If an socket.error is raised and auto_connect is enabled,
        a reconnect will be executed.

        Parameters
        ----------
        data : bytes
            Sends the given bytes to the socket.
        """
        if not self._connected:
            return
        try:
            self.sock.sendall(data)
        except socket.error:
            self._connected = False
            self.logger.error("error send data")
            if self.auto_reconnect:
                self.logger.error("reconnecting ...")
                self.connect()

    def receive(self, bytes_to_receive: int = 4096) -> bytes:
        """ Receives messages from the socket. If an socket.error is raised and auto_connect is enabled,
        a reconnect will be executed, otherwise an empty byte string will be returned.

        Parameters
        ----------
        bytes_to_receive : int, default 4096
            Reads the number bytes from the socket. Returns fewer bytes than bytes_to_receive if fewer are available.

        Returns
        -------
        bytes
            The received data from the socket. Or an empty byte string if socket.error is raised.
        """
        if not self._connected:
            return b''
        try:
            data = self.sock.recv(bytes_to_receive)
            return data
        except socket.error:
            self._connected = False
            self.logger.error("error receiving data")
            if self.auto_reconnect:
                self.logger.error("reconnecting ...")
                self.connect()
            return b''

    def receive_until(self, bytes_to_receive: int = 4096, delimiter: bytes = '\n', timeout: float = 1.0) -> bytes:
        """ Receives messages from the socket until the given delimiter is recognized.

       The data will be split at the delimiter. The delimiter will be removed from the message and returned.
       If the received message contains a message after the delimiter, it will be stored in a buffer
       and prepended to the next message.
       If an socket.error is raised and auto_connect is enabled,
       a reconnect will be executed, otherwise an empty byte string will be returned.

        Parameters
        ----------
        bytes_to_receive : int, default 4096
            Reads the number bytes from the socket. Returns fewer bytes than bytes_to_receive if fewer are available.
        delimiter : bytes, default '\\n'
            Splits the read data at the delimiter
        timeout : float, default 1.0
            The maximum time this function will wait until a ClientTimeoutError is raised.

        Returns
        -------
        bytes
            The received data from the socket. Or an empty byte string if socket.error is raised.

        Raises
        ------
        ClientTimeoutError
            Raises if no data was read or no delimiter was found withing the given time.
        """
        timeout_start = time.time()
        while time.time() < timeout_start + timeout:
            chunk = self.receive(bytes_to_receive)
            if not chunk:
                break
            if delimiter not in chunk:
                self.buffer.append(chunk)
                continue
            data = chunk.split(delimiter, maxsplit=1)
            self.buffer.append(data[0])
            ret = self.buffer.copy()
            self.buffer = [data[1]]

            return b''.join(ret)

        raise ClientTimeoutError("timeout while receiving data")

    def close(self):
        """ Closes the socket connection if it open
        """
        if not self._connected:
            return
        self._connected = False
        self.sock.close()
