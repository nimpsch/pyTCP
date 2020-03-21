import socket
import unittest
from unittest import mock

import pytest
from mock_server import MockServer

from pyTCP.client import TcpClient
from pyTCP.client_errors import ClientTimeoutError


class TcpClientTest(unittest.TestCase):

    def setUp(self):
        with mock.patch('socket.socket') as mock_socket:
            self.client = TcpClient("127.0.0.1", port=12345)
            self.client.connect()
            self.mock_socket = mock_socket

    def tearDown(self):
        self.client.close()

    @pytest.mark.timeout(1)
    def test_send_with_server(self):
        mock_server = MockServer("127.0.0.1", 12345)
        mock_server.start_server()
        client = TcpClient("127.0.0.1", port=12345)
        client.connect()

        data_to_send = b"Test message"
        client.send(data_to_send)
        ret = mock_server.get_message()
        self.assertEqual(data_to_send, ret)

        mock_server.stop_server()
        client.close()

    @pytest.mark.timeout(1)
    def test_receive_parts(self):
        mock_server = MockServer("127.0.0.1", 12345)
        mock_server.start_server()
        client = TcpClient("127.0.0.1", port=12345)
        client.connect()

        data_to_send = b"Test message\nHello"
        client.send(data_to_send)
        ret = client.receive_until(bytes_to_receive=1, delimiter=b'\n')
        self.assertEqual(b"Test message", ret)
        self.assertEqual(b"", client.buffer[0])

        mock_server.stop_server()
        client.close()

    def test_connect_and_receive(self):
        data_to_send = "Test message"
        self.mock_socket.return_value.recv.return_value = data_to_send
        self.client.sock.connect.assert_called_with(("127.0.0.1", 12345))
        self.assertEqual(self.client.receive(), data_to_send)

    def test_send(self):
        data_to_send = b"Test message"
        self.mock_socket.sendto(data_to_send)
        self.client.send(data_to_send)
        self.client.sock.sendall.assert_called_with(data_to_send)

    def test_connect_and_receive_until(self):
        data_to_send = b"Test message\nHello"
        self.mock_socket.return_value.recv.return_value = data_to_send
        self.client.sock.connect.assert_called_with(("127.0.0.1", 12345))

    def test_receive_until_empty(self):
        data_to_send = b""
        self.mock_socket.return_value.recv.return_value = data_to_send
        self.client.sock.connect.assert_called_with(("127.0.0.1", 12345))
        with pytest.raises(ClientTimeoutError):
            self.client.receive_until(delimiter=b'\n', timeout=0.1)

    def test_is_connected(self):
        self.assertTrue(self.client.is_connected)
        self.client.close()
        self.assertFalse(self.client.is_connected)

    def test_reconnect_on_send_with_socket_error(self):
        self.client.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect = mock.MagicMock()
        self.client.send(b"Test message")
        self.assertFalse(self.client.is_connected)
        self.assertTrue(self.client.connect.called)

    def test_no_reconnect_on_send_with_socket_error(self):
        self.client.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect = mock.MagicMock()
        self.client.auto_reconnect = False
        self.client.send(b"Test message")
        self.assertFalse(self.client.is_connected)
        self.assertFalse(self.client.connect.called)

    def test_reconnect_on_receive_with_socket_error(self):
        self.client.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect = mock.MagicMock()
        self.client.receive()
        self.assertFalse(self.client.is_connected)
        self.assertTrue(self.client.connect.called)

    def test_on_receive_with_socket_error(self):
        self.client.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect = mock.MagicMock()
        self.client.auto_reconnect = False
        ret = self.client.receive()
        self.assertEqual(b"", ret)
        self.assertFalse(self.client.is_connected)
        self.assertFalse(self.client.connect.called)

    def test_throw_on_timeout(self):
        with pytest.raises(ClientTimeoutError):
            self.client.receive_until(timeout=0)

    def test_close(self):
        self.client.sock = mock.MagicMock()
        self.client.close()
        self.assertFalse(self.client.is_connected)
        self.assertTrue(self.client.sock.close.called)
        self.client.sock = mock.MagicMock()
        self.client.close()
        self.assertFalse(self.client.sock.close.called)

    def test_throws_on_connect(self):
        with mock.patch('socket.socket'):
            client = TcpClient("127.0.0.1", port=12345)
            client.sock.connect = mock.MagicMock(side_effect=socket.error)
            with pytest.raises(ClientTimeoutError):
                client.connect(timeout=0.6)
                assert 2 == client.sock.connect.call_count

    def test_send_returns_if_not_connected(self):
        with mock.patch('socket.socket') as _:
            client = TcpClient("127.0.0.1", port=12345)
            client.send(b"Test")
            assert client.sock.sendall.call_count == 0

    def test_recv_returns_if_not_connected(self):
        with mock.patch('socket.socket') as _:
            client = TcpClient("127.0.0.1", port=12345)
            ret = client.receive()
            assert client.sock.recv.call_count == 0
            assert ret == b''


if __name__ == "__main__":
    unittest.main()
