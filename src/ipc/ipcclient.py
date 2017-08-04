import asyncio


class IpcClient():

    def __init__(self, loop, port=1234):
        self._port = port
        self._loop = loop
        self._ondata = None
        self._ondisconnect = None

    def set_ondata_observer(self, observer):
        self._ondata = observer

    def on_data(self, data):
        if self._ondata:
            self._ondata(data)

    def set_ondisconnect_observer(self, observer):
        self._ondisconnect = observer

    def on_disconnect(self):
        if self._ondisconnect:
            self._ondisconnect()

    def write(self, data):
        self._client.write(data)

    def start(self):
        coro = self._loop.create_connection(lambda: IpcClientProtocol(self),
                                            '127.0.0.1', self._port)
        self._loop.run_until_complete(coro)


class IpcClientProtocol(asyncio.Protocol):
    def __init__(self, client):
        self._client = client

    def write(self, data):
        if self._transport:
            self._transport.write(data.encode())

    def connection_made(self, transport):
        self._transport = transport
        self._client._client = self

    def data_received(self, data):
        self._client.on_data(data.decode())

    def connection_lost(self, exc):
        self._client.on_disconnect()
