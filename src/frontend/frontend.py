#! /usr/bin/python3
import asyncio
import os
import signal
import subprocess
import sys


def end_signal_handler(signal, frame):
    global loop
    loop.stop()
    sys.exit()


class AutomeventFrontend(asyncio.Protocol):
    def __init__(self, loop):
        self.loop = loop

    def connection_made(self, transport):
        pass

    def data_received(self, data):
        print('Data received: {!r}'.format(data.decode()))
        execute(data.decode())

    def connection_lost(self, exc):
        print('The server closed the connection')
        print('Stop the event loop')
        self.loop.stop()


def execute(cmd):
    env = os.environ.copy()
    # env['SHELL'] = '/usr/bin/fish'
    # env['PWD'] = '/home/user'
    subprocess.Popen(cmd.split(' '), env=env, start_new_session=True)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, end_signal_handler)
    signal.signal(signal.SIGTSTP, end_signal_handler)
    signal.signal(signal.SIGTERM, end_signal_handler)
    loop = asyncio.get_event_loop()
    coro = loop.create_connection(lambda: AutomeventFrontend(loop),
                                  '127.0.0.1', 1234)
    loop.run_until_complete(coro)
    loop.run_forever()
    loop.close()
