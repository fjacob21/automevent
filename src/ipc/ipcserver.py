import asyncio


class IpcServer():

    def __init__(self, loop, port=1234):
        self._port = port
        self._loop = loop
        self._clients = []
        self._ondata = None
        self._ononnect = None
        self._ondisconnect = None

    def set_ondata_observer(self, observer):
        self._ondata = observer

    def on_data(self, data, remote):
        if self._ondata:
            self._ondata(data, remote)

    def set_onconnect_observer(self, observer):
        self._onconnect = observer

    def on_connect(self, remote):
        if self._onconnect:
            self._onconnect(remote)

    def set_ondisconnect_observer(self, observer):
        self._ondisconnect = observer

    def on_disconnect(self, remote):
        if self._ondisconnect:
            self._ondisconnect(remote)

    def write(self, data):
        for client in self._clients:
            client.write(data)

    def start(self):
        coro = self._loop.create_server(lambda: IpcServerProtocol(self), port=self._port)
        self._server = self._loop.run_until_complete(coro)

    def add_client(self, client):
        self._clients.append(client)

    def remove_client(self, client):
        self._clients.remove(client)


class IpcServerProtocol(asyncio.Protocol):

    def __init__(self, server):
        self._server = server

    def write(self, data):
        if self._transport:
            self._transport.write(data.encode())

    def connection_made(self, transport):
        self._transport = transport
        self._peername = transport.get_extra_info("peername")
        self._server.add_client(self)
        self._server.on_connect(self._peername)

    def data_received(self, data):
        self._server.on_data(data.decode(), self._peername)

    def connection_lost(self, ex):
        self._server.remove_client(self)
        self._server.on_disconnect(self._peername)
