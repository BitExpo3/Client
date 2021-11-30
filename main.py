# By BitExpo3
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


# Server IP and PORT coming soon
SERVER = socket.gethostbyname(socket.gethostname()) # SERVER IP AS STR ("127.0.0.1")
PORT = 5052 # SERVER PORT AS INT (5000)
ADDR = (SERVER, PORT)

HEADER = 64
FORMAT = "utf-8"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(2)

RUNNING = True
GAMEVERSION = 1

DataDict = {
    "name": "x",
    "inv": [],
    "inv_max": 0.0,
    "stats": {
        "str": 0,
        "def": 0
    }
}
DATA = DataDict.copy()

TUI = {
    "msg": ""
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

class DataClass:
    name = "test"
    inv = [["c",2],["b",3]]
    inv_max = 10.0
    stats = {
        "str": 10,
        "def": 1
    }

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
        wbar.addstr(2,1,f"Name: " + str(data["name"]) + " // Inv: " + str(data["inv_max"]))
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
    return string

class ProtocolClass():
   SOC = "s" # socket management
   ACC = "a" # account type command
   REA = "r" # command with read nature
   WRI = "w" # command with write nature
msg_types = ProtocolClass

def recieve():
    global RUNNING
    global DATA
    global state, substate
    while True:
        if not RUNNING:
            print("Closing Thread..")
            return
        try:
            msg_length = client.recv(HEADER).decode(FORMAT)
            #print(msg_length)
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
                            print("- Go to: [https://github.com/test/test] for the latest release!")
                            print("('\\n' to leave)")
                            RUNNING = False
                            send(msg_types.SOC + "\n!")
                            sys.exit()
                        else:
                            print("Client Up To Date! (v" + str(GAMEVERSION) + ")")
                elif msg[0] == msg_types.REA:
                    data_dict = json.loads(str(msg[2]).replace("'","\""))
                    DATA[msg[1]] = data_dict[0]
                elif msg[0] == msg_types.ACC:
                    if len(msg) > 1:
                        if msg[1] == "0":
                            TUI["msg"] = ("Invalid email syntax!")
                        elif msg[1] == "1":
                            TUI["msg"] = ("Email or Password incorrect!")
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
                    #else:
                        #print("[ACCOUNT] Please login to account!")
        except TimeoutError:
            pass

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))

    client.send(send_length)
    client.send(message)
    #print(client.recv(2048).decode(FORMAT))

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
                msg = getstring(30,"Command","★a ✪ ✎a ♫")
            elif key == ord("t"): 
                msg = getstring(50,"Command","")
                msg = msg.lower().strip()
                #print(msg)

                if msg == "login":
                    email = getstring(30,"Login","EMail")
                    password = getstring(20,"Login","Pass")
                    send(msg_types.ACC + "\n0\n" + email + "\n" + password)
                    #else:
                    #    TUI["msg"] = ("!login [email] [password]")
                        #print("[ACCOUNT] Please provide email and password!")
                elif msg == "register":
                    if len(msg) > 2:
                        if msg[2].isalnum() & len(msg[2]) <= 20 & len(msg[2]) >= 5:
                            if state == "login":
                                send(msg_types.ACC + "\n1\n" + msg[1] + "\n" + msg[2])
                            else:
                                TUI["msg"] = ("You can not do this while logged in!")
                        else:
                            TUI["msg"] = ("Password must be alphanumeric, and 5 - 20 characters long!")
                    else:
                        TUI["msg"] = ("register [email] [password]")
                elif msg == "token":
                    if len(msg) > 1:
                        if state == "login":
                            send(msg_types.ACC + "\n2\n" + msg[1])
                        else:
                            TUI["msg"] = ("You can not do this while logged in!")
                    else:
                        TUI["msg"] = ("token [token]")
                #elif len(msg) > 1 and msg[0] == "r":
                #    #print("[SENT] Retrieving data from server!")
                #    send(msg_types.REA + "\n" + msg[1])
                #elif len(msg) > 1 and msg[0] == "w":
                #    tmp2 = ""
                #    tmp = msg
                #    tmp.pop(0)
                #    for i in tmp:
                #        tmp2 = tmp2 + i + " "
                #    send(msg_types.WRI + "\n" + tmp2)
            

            if key == 546: 
                resize(stdscr)
                update(DATA)
            else:
                update(DATA)
                if key != -1:
                    TUI["msg"] = ""

wrapper(main)