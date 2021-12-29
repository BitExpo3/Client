# /  ┌─────────────┐ \  #
# |==│ By BitExpo3 │==| #
# \  └─────────────┘ /  #

import socket
import threading
import sys
import json
import curses
from curses import wrapper
import yaml
import os

wmain = None
wside = None
wbar = None
winy, winx = None, None
state = ""

# Official server IP & PORT coming soon!
SERVER = socket.gethostbyname(socket.gethostname())     # SERVER IP:    STR ("127.0.0.1")
PORT = 5052                                             # SERVER PORT:  INT (5000)
ADDR = (SERVER, PORT)

HEADER = 64
FORMAT = "utf-8"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(2)

RUNNING = True
GAMEVERSION = 1
LOADED = False

DATA = {}
TUI = {
    "msg": "",
    "chat": []
}

class YamlManager:
    def read(directory):
        with open(directory) as file:
            try:
                output = yaml.safe_load(file)   
                return output
            except yaml.YAMLError as exc:
                print(exc)
                return False

    def write(directory,data):
        with open(directory, 'w') as file:
            yaml.dump(data, file)

    def dir(directory):
        tmp = []
        for files in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, files)):
                tmp.append(files)
        return tmp

    def file(directory):
        tmp = []
        for files in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, files)):
                tmp.append(files)
        return tmp

    def name(file):
        return file.split(".")[0]
file = YamlManager

class ColorClass:
    GREEN = None
    RED = None
    YELLOW = None
    BLUE = None
    PURPLE = None
    def init(self):
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        self.GREEN = curses.color_pair(1)
        self.RED = curses.color_pair(2)
        self.YELLOW = curses.color_pair(3)
        self.BLUE = curses.color_pair(4)
        self.PURPLE = curses.color_pair(5)
color = ColorClass

class ProtocolClass():
   SOC = "s" # socket management
   ACC = "a" # account type command
   REA = "r" # command with read nature
   WRI = "w" # command with write nature
msg_types = ProtocolClass

def resize(stdscr):
    global wmain, wside, wbar, winy, winx
    winy,winx = stdscr.getmaxyx()
    wmain = curses.newwin(winy-3,winx-29,3,29)
    wside = curses.newwin(winy-3,30,3,0)
    wbar = curses.newwin(4,winx,0,0)

def update(data):
    global state, substate
    wmain.clear()
    wside.clear()
    wbar.clear()


    wmain.border(ord("│"),ord("│"),ord("─"),ord("─"),ord("─"),ord("┘"),ord("┘"),ord("┘"))
    wside.border(ord("│"),ord("│"),ord("─"),ord("─"),ord("└"),ord("─"),ord("└"),ord("┘"))
    wbar.border(ord("│"),ord("│"),ord("─"),ord("─"),ord("┌"),ord("┐"),ord("└"),ord("┘"))

    wbar.addstr(1,1,f"AnotherRPG")
    if state == "login":
        wbar.addstr(2,1,"Log-In to account!")
    else:
        if LOADED:
            print(data)
            wbar.addstr(2,1,f"Inv: " + str(data["weight"]))
            amount = 0
            for i in range(len(TUI["chat"])):
                if amount >= winy-5:
                    break
                wmain.addstr((winy-5)-i,1,TUI["chat"][i][0] + ": " + TUI["chat"][i][1])
                amount += 1
    if TUI["msg"] != "":
        wbar.addstr(1,11," // " + TUI["msg"])


    wbar.refresh()
    wmain.refresh()  
    wside.refresh()
    curses.curs_set(0)

def getstring(max,title,var):
    wmain.hline(winy-6, 1, ord("─"), winx-31)
    wmain.addstr(winy-6,2,title)
    wmain.addstr(winy-5,1," "*(winx-31))
    wmain.addstr(winy-5,1,var + ": ")
    wmain.addstr(winy-6,winx-30,"┘")
    wmain.addstr(winy-5,winx-(36 + len(str(max))),f"(Max {max})")
    wmain.refresh()
    wmain.move(winy-5,3 + len(str(var)))
    curses.echo()
    string = wmain.getstr(max).decode().strip()
    curses.noecho()
    return str(string)

def recieve():
    global LOADED
    global RUNNING
    global DATA
    global state, substate
    while True:
        if not RUNNING:
            print("Closing Thread..")
            return
        try:
            msg_length = client.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = client.recv(msg_length).decode(FORMAT).split("\n")

                if msg[0] == msg_types.SOC:
                    if msg[1] == "!":
                        print("Server Closed!")
                        RUNNING = False
                        sys.exit()
                    elif msg[1].startswith("v"):
                        tmp = str(msg[1].split(" ")[1])
                        if str(tmp) != str(GAMEVERSION):
                            print("Wrong version! Server: v" + str(tmp) + " Client: v" + str(GAMEVERSION))
                            print("- Go to: [https://github.com/BitExpo3/Client] for the latest release!")
                            print("('\\n' to leave)")
                            RUNNING = False
                            send(msg_types.SOC + "\n!")
                            sys.exit()
                        else:
                            print("Client Up To Date! (v" + str(GAMEVERSION) + ")")
                elif msg[0] == msg_types.REA:
                    if msg[1].startswith("msg "):
                        tmp = msg[1].split(" ")
                        
                        TUI["chat"].insert(0,[tmp[1],msg[1][len("msg " + tmp[1] + " "):]])
                    else:
                        if msg[1] == "FINAL":
                            LOADED = True
                        else:
                            data_dict = json.loads(str(msg[2]).replace("'","\""))
                            DATA[msg[1]] = data_dict[0]
                elif msg[0] == msg_types.ACC:
                    if len(msg) > 1:
                        if msg[1] == "0":
                            TUI["msg"] = ("Invalid email syntax!")
                        elif msg[1] == "1":
                            TUI["msg"] = ("User or Password incorrect!")
                        elif msg[1] == "2":
                            TUI["msg"] = ("Logged in to account!")
                            state = "game"
                            send(msg_types.REA + "\n" + "all")
                        elif msg[1] == "3":
                            TUI["msg"] = ("Account already exists!")
                        elif msg[1] == "4":
                            TUI["msg"] = ("Verification email sent! Please send token with '!token [token]'")
                        elif msg[1] == "5":
                            TUI["msg"] = ("You do not have a pending token!")
                        elif msg[1] == "6":
                            TUI["msg"] = ("Token is not valid!")
                        elif msg[1] == "7":
                            TUI["msg"] = ("You have created an account!")
                            state = "game"
                            send(msg_types.REA + "\n" + "all")
                            TUI["msg"] = ("Logged in to account!")
                        elif msg[1] == "8":
                            TUI["msg"] = ("You must be logged in to do this!")
                #update(DATA)
        except TimeoutError:
            pass

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))

    client.send(send_length)
    client.send(message)

def main(stdscr):
    global RUNNING
    global wmain, wside, wbar
    global winy, winx

    global state, TUI

    color.init(color)
    resize(stdscr)
    
    stdscr.timeout(100)

    worked = True
    try:
        client.connect(ADDR)
    except:
        print("[ERROR] Connection unsucessful, please try again later.")
        worked = False
        RUNNING = False
        sys.exit()
        input()
    if worked:
        state = "login"
        TUI["msg"] = ("Connected to server!")

        thread1 = threading.Thread(target=recieve)
        thread1.isDaemon = True
        thread1.start()
        
        while RUNNING:
            try:
                key = stdscr.getch()
            except curses.error:
                key = None

            if key == ord("q"):
                RUNNING = False
                send(msg_types.SOC + "\n!")
                sys.exit()
            elif key == ord("m"):
                msg = getstring(50,"Message","")
                send(msg_types.WRI + "\nmsg " + msg)
            elif key == ord("t"): 
                msg = getstring(50,"Command","")
                msg = msg.lower().strip()

                if msg == "login":
                    name = getstring(30,"Login","User")
                    password = getstring(20,"Login","Pass")
                    send(msg_types.ACC + "\n0\n" + name + "\n" + password)
                elif msg == "register":
                    if state == "login":
                        email = getstring(30,"Register","EMail")
                        password = getstring(20,"Register","Pass")
                        name = getstring(20,"Register","User")
                        print(password)
                        print(password.isalnum())
                        print(len(password) <= 20)
                        print(len(password) >= 5)

                        if password.isalnum() and len(password) <= 20 and len(password) >= 5 & name.isalnum() & len(name) <= 20 & len(name) >= 3:
                            send(msg_types.ACC + "\n1\n" + email + "\n" + password + "\n" + name)
                        else:
                            TUI["msg"] = ("Password and User must be alphanumeric, and 5 - 20 characters long!")
                    else:
                        TUI["msg"] = ("You can not do this while logged in!")
                elif msg == "token":
                    token = getstring(30,"Register","Token")
                    if state == "login":
                        send(msg_types.ACC + "\n2\n" + token)
                    else:
                        TUI["msg"] = ("You can not do this while logged in!")
                else:
                    TUI["msg"] = "Unknown command."
            if key == 546: 
                resize(stdscr)
                update(DATA)
            else:
                update(DATA)
wrapper(main)