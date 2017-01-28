#!/usr/bin/env python
import sys
import signal
import subprocess
import socket
import os
import time
import tempfile
import json
import select
class termuxmpv:
    def signal_handler(self,signal, frame):
        pass
    def __init__(self,args):
        signal.signal(signal.SIGINT, self.signal_handler)
        self.args=args
        self.pause=False
        self.initFifo()
        self.createSocket()
        self.startProcess()
        self.getSocket()
        self.monitor()
    def __del__(self):
        self.cleanup()

    def initFifo(self):
        self.notificationId="termuxMpv.{}".format(time.time())
        self.fifoname="/data/data/com.termux/files/usr/tmp/{}".format(self.notificationId)
        os.mkfifo(self.fifoname)
        self.fifo = os.open(self.fifoname, os.O_RDONLY | os.O_NONBLOCK)
    def startProcess(self):
        self.mpvproc=subprocess.Popen(['mpv', '--input-ipc-server', self.sockpath] + self.args ,stdin=sys.stdin) 
    def createSocket(self):
        fd, self.sockpath = tempfile.mkstemp(prefix="mpv.")
        os.close(fd)
        os.remove(self.sockpath)
    def getSocket(self):
        while self.isRunning():
            time.sleep(0.1)
            try:
                self.sock = socket.socket(socket.AF_UNIX)
                self.sock.connect(self.sockpath)
            except (FileNotFoundError, ConnectionRefusedError):
                continue
            else:
                break
        else:
            sys.exit(1)
    def isRunning(self):
        return self.mpvproc.poll() is None
    def cleanup(self):
        self.fifo.close()
        os.remove(self.fifoname)
        if self.notificationId:
            command=["termux-notification-remove",self.notificationId]
            output=subprocess.call(command)
        if self.sockpath:
            try:
                os.remove(self.sockpath)
            except OSError:
                pass
    def monitor(self):
        while self.isRunning():
            # time.sleep(1)
            b=True
            buf = b""
            while b:
                b=None
                r, w, e = select.select([self.sock], [], [], 1)
                if r:
                    b = self.sock.recv(1024)
                if not b:
                    break
                buf += b
            buf=buf.decode("utf-8")
            newline = buf.find("\n")
            while newline >= 0:
                message = buf[:newline + 1]
                buf = buf[newline + 1:]
                newline = buf.find("\n")

                self.processMessage(message)
            command=""
            while True:
                part=os.read(self.fifo,1024).decode("utf-8")
                command="{}{}".format(command,part)
                if not part:
                    break
            if command:
                self.sendCommand(command)
    def sendCommand(self,command):
        command=command.strip()
        if command=="prev":
            self.sendMessage(["keypress","<"])
        if command=="next":
            self.sendMessage(["keypress",">"])
        if command=="pause":
            self.sendMessage(["keypress","p"])
        if command=="updateNotification":
            self.updateNotification()
    def sendMessage(self,message):
        data={}
        data["command"]=message
        data=json.dumps(data)
        data="{}\n".format(data)
        data=data.encode("utf-8")
        while data:
            size = self.sock.send(data)
            if size == 0:
                print("Socket error", file=sys.stderr)
            data = data[size:]

    def processMessage(self, message):
        try:
            message=json.loads(message)
        except:
            pass
        if "event" in message:
            if message["event"]=="metadata-update":
                self.sendMessage(["get_property","metadata"])
            if message["event"]=="pause":
                self.pause=True
                self.updateNotification()
            if message["event"]=="unpause":
                self.pause=False
                self.updateNotification()
        elif "data" in message:
            if message["data"]:
                if "title" in message["data"]:
                    self.metadata=message["data"]
                    self.updateNotification()

    def updateNotification(self):
        playbutton="█ █"
        if self.pause:
            playbutton="▶"
        command=[
            "termux-notification",
            "--id", self.notificationId,
            "--title", self.metadata["title"],
            "--content", "{}, {}".format(self.metadata["artist"], self.metadata["album"]),
            # "--led-color 00ffff",
            # "--vibrate 300,150,300",
            "--priority", "max",
            "--action", ";".join([
                "am start --user 0 -n com.termux/com.termux.app.TermuxActivity",
                "echo 'updateNotification'> {}".format(self.fifoname)
                ]),
            "--button1", "◀◀",
            "--button1-action","echo 'prev'> {}".format(self.fifoname),
            "--button2", playbutton,
            "--button2-action","echo 'pause'> {}".format(self.fifoname),
            "--button3", "▶▶",
            "--button3-action","echo 'next'> {}".format(self.fifoname),
        ]
        output=subprocess.call(command)
def main(args=None):
    if args is None:
        args = sys.argv[1:]
    termuxmpv(args)
if __name__ == "__main__":
    main()


