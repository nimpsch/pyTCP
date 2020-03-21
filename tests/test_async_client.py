import asyncio
from unittest import mock

import pytest
from mock_server import MockServer

from pyTCP.async_client import TcpClient
from pyTCP.client_errors import ClientTimeoutError


async def async_magic():
    pass


mock.MagicMock.__await__ = lambda x: async_magic().__await__()


class TestAsyncTcpClient:

    @pytest.yield_fixture
    def event_loop(self):
        """
        This is needed for correct functioning of the test_client of aiohttp together with
        pytest.mark.asyncio pytest-asyncio decorator. For more info check the following link:
        https://github.com/KeepSafe/aiohttp/issues/939
        """
        loop = asyncio.get_event_loop()
        loop._close = loop.close
        loop.close = lambda: None
        yield loop
        loop.close = loop._close

    @pytest.mark.timeout(1)
    @pytest.fixture
    async def setup(self):
        mock_server = MockServer("127.0.0.1", 12345)
        mock_server.start_server()
        client = TcpClient("127.0.0.1", port=12345)
        await client.connect()

        yield client, mock_server
        # teardown
        client.close()
        mock_server.stop_server()

    @pytest.mark.asyncio
    async def test_send_with_server(self, setup):
        client, mock_server = setup
        data_to_send = b"Test message"
        await client.send(data_to_send)
        ret = mock_server.get_message()
        assert ret == data_to_send

    @pytest.mark.asyncio
    async def test_receive_with_server(self, setup):
        client, mock_server = setup
        data_to_send = b"Test message"
        await client.send(data_to_send)
        data = await client.receive()
        assert data == data_to_send

    @pytest.mark.asyncio
    async def test_connect_and_receive_until(self, setup):
        client, mock_server = setup
        data_to_send = b"Test message\nHello"
        await client.send(data_to_send)
        ret = await client.receive_until(delimiter=b'\n')
        assert ret == b"Test message"
        assert client.buffer[0] == b"Hello"

    @pytest.mark.asyncio
    async def test_connect_and_receive_parts(self, setup):
        client, mock_server = setup
        data_to_send = b"Test message\nHello"
        await client.send(data_to_send)
        ret = await client.receive_until(bytes_to_receive=1, delimiter=b'\n')
        assert ret == b"Test message"
        assert client.buffer[0] == b""

    @pytest.mark.asyncio
    async def test_reconnect_on_send_with_socket_error(self, setup):
        client, mock_server = setup
        client.writer.write = mock.MagicMock(side_effect=ConnectionRefusedError)
        client.connect = mock.MagicMock()
        await client.send(b"Test message")
        assert not client.is_connected
        assert client.connect.called

    @pytest.mark.asyncio
    async def test_no_reconnect_on_send_with_socket_error(self, setup):
        client, mock_server = setup
        client.writer.write = mock.MagicMock(side_effect=ConnectionRefusedError)
        client.connect = mock.MagicMock()
        client.auto_reconnect = False

        await client.send(b"Test message")
        assert not client.is_connected
        assert not client.connect.called

    @pytest.mark.asyncio
    async def test_reconnect_on_receive_with_socket_error(self, setup):
        client, mock_server = setup
        client.reader.read = mock.MagicMock(side_effect=ConnectionRefusedError)
        client.connect = mock.MagicMock()

        await client.receive()
        assert not client.is_connected
        assert client.connect.called

    @pytest.mark.asyncio
    async def test_no_reconnect_on_receive_with_socket_error(self, setup):
        client, mock_server = setup
        client.reader.read = mock.MagicMock(side_effect=ConnectionRefusedError)
        client.auto_reconnect = False
        client.connect = mock.MagicMock()

        ret = await client.receive()
        assert ret == b""
        assert not client.is_connected
        assert not client.connect.called

    @pytest.mark.asyncio
    async def test_receive_until_raises(self, setup):
        client, mock_server = setup
        with pytest.raises(ClientTimeoutError):
            await client.receive_until(delimiter=b'\n', timeout=0)

    @pytest.mark.asyncio
    async def test_receive_until_empty(self, setup):
        client, mock_server = setup
        client.reader.read = mock.MagicMock(side_effect=ConnectionRefusedError)
        data_to_send = b""
        client.reader.read.return_value.recv.return_value = data_to_send
        with pytest.raises(ClientTimeoutError):
            await client.receive_until(delimiter=b'\n', timeout=0.1)

    @pytest.mark.asyncio
    async def test_connect(self, setup):
        client, mock_server = setup
        assert client.is_connected
        client.close()
        assert not client.is_connected

    @pytest.mark.asyncio
    async def test_close(self, setup):
        client, mock_server = setup
        client.writer = mock.MagicMock()
        client.close()
        assert not client.is_connected
        assert client.writer.close.called
        client.writer = mock.MagicMock()
        client.close()
        assert not client.writer.close.called

    @pytest.mark.asyncio
    async def test_throws_on_connect(self):
        with mock.patch('asyncio.open_connection') as asyncio_mock:
            asyncio_mock.return_value = 1, 2
            asyncio_mock.side_effect = ConnectionRefusedError
            client = TcpClient("127.0.0.1", port=12345)
            with pytest.raises(ClientTimeoutError):
                await client.connect(timeout=0.6)
                assert asyncio.open_connection.call_count == 2

    @pytest.mark.asyncio
    async def test_send_returns_if_not_connected(self):
        client = TcpClient("127.0.0.1", port=12345)
        client.writer = mock.MagicMock(side_effect=ConnectionRefusedError)
        await client.send(b"Test")
        assert client.writer.write.call_count == 0

    @pytest.mark.asyncio
    async def test_recv_returns_if_not_connected(self):
        client = TcpClient("127.0.0.1", port=12345)
        client.reader = mock.MagicMock(side_effect=ConnectionRefusedError)
        ret = await client.receive()
        assert 0 == client.reader.read.call_count
        assert ret == b''
