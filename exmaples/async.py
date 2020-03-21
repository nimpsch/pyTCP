import asyncio

from pyTCP import AsyncTcpClient, EchoServer


async def main():
    echo_server = EchoServer("127.0.0.1", 12345)
    echo_server.start_server()
    client = AsyncTcpClient("127.0.0.1", 12345)
    await client.connect()

    data_to_send = b"Test message"
    await client.send(data_to_send)
    data = await client.receive()
    assert data == data_to_send

    echo_server.stop_server()
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
