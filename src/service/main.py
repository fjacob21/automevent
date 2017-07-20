#! /usr/bin/python3

import asyncio
import evdev
from evdev import UInput
from evdev import ecodes
import os
from keyboardevent import KeyboardEvent
import signal
import subprocess
import pwd

clients = []
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
devices = [dev for dev in devices if 2 not in dev.capabilities()]
end = False
print(devices)
print('Starting')
# print(os.getlogin())
ui = UInput()

current_events = []
# {'ids': ['KEY_LEFTSHIFT','Razer Razer Naga.KEY_1'], 'action': 'gnome-terminal'},
# actions = [{'ids': ['Razer Razer Naga.KEY_1'], 'action': 'runuser fjacob -c gnome-terminal'},
#            {'ids': ['Razer Razer Naga.KEY_2'], 'action': 'runuser fjacob -c nautilus'},
#            {'ids': ['Razer Razer Naga.KEY_3'], 'action': 'runuser fjacob -c /opt/google/chrome/chrome'},
#            {'ids': ['Razer Razer Naga.KEY_4'], 'action': 'runuser fjacob -c /home/fjacob/winlinclipcopy.sh'},
#            {'ids': ['Razer Razer Naga.KEY_5'], 'action': 'runuser fjacob -c /home/fjacob/winlinclippaste.sh'},
#            {'ids': ['KEY_LEFTSHIFT', 'Razer Razer Naga.KEY_1'], 'action': 'exit'}]
actions = [{'ids': ['Razer Razer Naga.KEY_1'], 'action': 'gnome-terminal --working-directory=~/'},
           {'ids': ['Razer Razer Naga.KEY_2'], 'action': 'nautilus'},
           {'ids': ['Razer Razer Naga.KEY_3'], 'action': '/opt/google/chrome/chrome'},
           {'ids': ['Razer Razer Naga.KEY_4'], 'action': 'sh -c /home/fjacob/winlinclipcopy.sh'},
           {'ids': ['Razer Razer Naga.KEY_5'], 'action': 'sh -c /home/fjacob/winlinclippaste.sh'},
           {'ids': ['KEY_LEFTSHIFT', 'Razer Razer Naga.KEY_1'], 'action': 'exit'}]


def end_signal_handler(signal, frame):
    global end, loop
    end = True
    loop.stop()


def keydown(l, key):
    if key in l:
        return l
    l.append(key)
    return l


def keyup(l, key):
    if key not in l:
        print('Not in down')
        return l
    l.remove(key)
    return l


def demote(user_uid, user_gid):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)
    return result


def execute_action(events):
    for action in actions:
        if len(events) == len(action['ids']):
            found = True
            for i in range(len(events)):
                if events[i].find(action['ids'][i]) < 0:
                    found = False
                    break
            if found:
                user_name = "fjacob"
                pw_record = pwd.getpwnam(user_name)
                user_name = pw_record.pw_name
                user_home_dir = pw_record.pw_dir
                # user_uid = pw_record.pw_uid
                # user_gid = pw_record.pw_gid
                env = os.environ.copy()
                env['HOME'] = user_home_dir
                env['LOGNAME'] = user_name
                env['DISPLAY'] = ':1'
                env['PWD'] = pw_record.pw_dir
                env['USER'] = user_name
                env['SHELL'] = '/usr/bin/fish'
                print('Action')
                if action['action'] == 'exit':
                    return True, True
                if len(clients) > 0:
                    print(clients)
                    for client in clients:
                        client.transport.write(action['action'].encode())
                else:
                    subprocess.Popen(action['action'].split(' '), env=env)
                # subprocess.Popen(action['action'].split(' '), start_new_session=True, preexec_fn=demote(user_uid, user_gid), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True, False
    return False, False


@asyncio.coroutine
def keyboard_events_monitor(device):
    global end
    print('Start', device)
    try:
        device.grab()
        while not end:
            events = yield from device.async_read()
            for event in events:
                execute = False
                if event.type == ecodes.EV_KEY:
                    ke = evdev.categorize(event)
                    key = ke.keycode
                    if isinstance(ke.keycode, list):
                        key = ke.keycode[0]

                    eventinfo = KeyboardEvent(device.info.vendor, device.info.product, device.name, key)

                    if ke.keystate == ke.key_down:
                        keydown(current_events, eventinfo.id)
                        execute, exit = execute_action(current_events)
                        end = exit
                    elif ke.keystate == ke.key_up:
                        keyup(current_events, eventinfo.id)
                    # elif ke.keystate == ke.key_hold:
                    #    state = 'hold'
                if not execute:
                    ui.write_event(event)
    except Exception as e:
        print('Exception', e)
    print('Terminated', device)
    loop.stop()
    device.ungrab()


class AutomeventProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        self.peername = transport.get_extra_info("peername")
        print("connection_made: {}".format(self.peername))
        clients.append(self)

    def data_received(self, data):
        print("data_received: {}".format(data.decode()))
        for client in clients:
            if client is not self:
                client.transport.write("{}: {}".format(self.peername, data.decode()).encode())

    def connection_lost(self, ex):
        print("connection_lost: {}".format(self.peername))
        clients.remove(self)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, end_signal_handler)
    signal.signal(signal.SIGTSTP, end_signal_handler)
    signal.signal(signal.SIGTERM, end_signal_handler)

    for device in devices:
        asyncio.async(keyboard_events_monitor(device))

    loop = asyncio.get_event_loop()
    coro = loop.create_server(AutomeventProtocol, port=1234)
    server = loop.run_until_complete(coro)

    for socket in server.sockets:
        print("serving on {}".format(socket.getsockname()))

    loop.run_forever()

    print('Terminated loop')
    for device in devices:
        device.ungrab()
        device.close()
