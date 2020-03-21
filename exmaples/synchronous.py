from pyTCP.client import TcpClient
from pyTCP.server import EchoServer

echo_server = EchoServer("127.0.0.1", 12345)
echo_server.start_server()
client = TcpClient("127.0.0.1", 12345)
client.connect()

data_to_send = b"Test message"
client.send(data_to_send)
client_received = client.receive()
server_received = echo_server.last_received
assert data_to_send == client_received
assert data_to_send == server_received

# or with a delimiter
data_to_send = b"Test\nmessage"
client.send(data_to_send)
client_received = client.receive_until(delimiter=b'\n')
assert b"Test" == client_received

echo_server.stop_server()
client.close()
