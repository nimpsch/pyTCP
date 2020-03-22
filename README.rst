.. image:: https://img.shields.io/pypi/v/pyTCP.svg
    :target: https://pypi.org/project/pyTCP

.. image:: https://img.shields.io/pypi/pyversions/pyTCP.svg
    :target: https://pypi.org/project/pyTCP

.. image:: https://readthedocs.org/projects/pytcp/badge/?version=latest
    :alt: ReadTheDocs
    :target: https://pytcp.readthedocs.io/

.. image:: https://travis-ci.org/nimpsch/pyTCP.svg?branch=master
    :alt: Travis
    :target: https://travis-ci.org/nimpsch/pyTCP

.. image:: https://img.shields.io/coveralls/github/nimpsch/pyTCP/master.svg
    :alt: Coveralls
    :target: https://coveralls.io/r/nimpsch/pyTCP
	
========
pyTCP
========


A small tcp package to send and receive tcp messages.

Installation
============

.. code-block:: bash

    pip install pyTCP

Usage
=====

synchronous:

.. code-block:: python

    from pyTCP import EchoServer, TcpClient

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

async:

.. code-block:: python

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

Note
====

This project has been set up using PyScaffold 3.2.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.

