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
import argparse
class termuxmpv:
    def signal_handler(self,signal, frame):
        pass
    def __init__(self,args):
        signal.signal(signal.SIGINT, self.signal_handler)
        self.args=args
        self.pause=False
        self.q=[]
        self.metadata={}
        self.initFifo()
        if not self.checkForSocket():
            self.createSocket()
        print(self.sockpath)
        self.startProcess()
        self.getSocket()
        self.first=True
        self.processMessage()
        self.first=False
        self.updateNotification()
        self.monitor()
    def __del__(self):
        self.cleanup()
    def checkForSocket(self):
        prev=""
        for arg in reversed(self.args):
            if arg=="--input-ipc-server":
                self.sockpath=prev
                return True
            elif arg.startswith("--input-ipc-server="):
                self.sockpath=arg.split("=")[1]
                return True

            prev=arg
        return False 
        
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
    def isRunning(self):
        
        if self.mpvproc.poll() is None:
            return True
        else:
            sys.exit(self.mpvproc.returncode)
        
    def cleanup(self):
        os.close(self.fifo)
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
            self.sendMessage(["keypress","<"],"keypress")
        if command=="next":
            self.sendMessage(["keypress",">"],"keypress")
        if command=="pause":
            self.sendMessage(["keypress","p"],"keypress")
        if command=="updateNotification":
            self.updateNotification()
    def sendMessage(self,message,msgprocessor):
        self.q.append(msgprocessor)
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

    def processMessage(self, message='{"event":""}'):
        try:
            message=json.loads(message)
        except:
            pass
        if "event" in message:
            if message["event"]=="metadata-update" or self.first:
                self.sendMessage(["get_property","metadata"],"metadata")
            if message["event"]=="file-loaded" or self.first:
                self.sendMessage(["get_property","filename"],"filename")
            if message["event"]=="pause":
                self.pause=True
                self.updateNotification()
            if message["event"]=="unpause":
                self.pause=False
                self.updateNotification()
        elif "data" in message:
            if self.q[0]:
                if self.q[0]=="metadata":
                    self.metadata=message["data"]
                    self.updateNotification()
                if self.q[0]=="filename":
                    self.filename=message["data"]
                    self.updateNotification()
                del self.q[0]
        elif "error" in message:
            del self.q[0]

    def updateNotification(self):
        # padding="           "
        #disable padding for now
        padding=""
        # playbutton="{}⏸{}".format(padding,padding)
        # prevbutton="{}⏮{}".format(padding,padding)
        # nextbutton="{}⏭{}".format(padding,padding)
        playbutton="{}❙❙{}".format(padding,padding)
        prevbutton="{}|◀◀{}".format(padding,padding)
        nextbutton="{}▶▶|{}".format(padding,padding)
        if self.pause:
            playbutton="{} ▶ {}".format(padding,padding)
        metadata={}
        for attr in ["album","artist","title"]:
            try:
                metadata[attr]=self.metadata[attr]
            except KeyError:
                metadata[attr]="None"
        try:
            filename=self.filename
        except AttributeError:
            filename="None"

        if metadata["title"]=="None":
            title=filename
        else:
            title=metadata["title"]
        command=[
            "termux-notification",
            "--id", self.notificationId,
            "--title", title,
            "--content", "{}, {}".format(metadata["artist"], metadata["album"]),
            # "--led-color 00ffff",
            # "--vibrate 300,150,300",
            "--priority", "max",
            "--action", ";".join([
                "am start --user 0 -n com.termux/com.termux.app.TermuxActivity",
                "echo 'updateNotification'> {}".format(self.fifoname)
                ]),
            "--button1", prevbutton,
            "--button1-action","echo 'prev'> {}".format(self.fifoname),
            "--button2", playbutton,
            "--button2-action","echo 'pause'> {}".format(self.fifoname),
            "--button3", nextbutton,
            "--button3-action","echo 'next'> {}".format(self.fifoname),
        ]
        output=subprocess.call(command)
def main(args=None):
    if args is None:
        args = sys.argv[1:]
    termuxmpv(args)
if __name__ == "__main__":
    main()


