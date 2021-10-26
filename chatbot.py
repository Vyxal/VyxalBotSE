# -*- coding: utf-8 -*-
## V 3.0
"""
ChangeLog
- V3.0 -
Rewrote chatbot.py using classes
Cleaned the code
Using pycryptodome instead of simplecrypt
Using websockets to listen top new events
"""
## Description
"""
A framework to set up a chat bot on StackExchange's chat rooms
"""

# Imports and initialization
import requests                 # making POST/GET requests
import json                     # fast JSON library
import time                     # timestamping events + measuring intervals between events / pausing the program / getting time since epoch for starting timestamps
import os                       # get local path, create folders
import Cryptodome.Cipher.DES    # encrypt and decrypt credidentials
import getpass                  # input password without outputing characters on CLI
import sys                      # exit program
import websocket                # listen to and send websockets from/to the chat
import threading                # multiprocessing - to make the rooms run in parallel
import datetime

EVENTS = {
        1: "EventMessagePosted",
        2: "EventMessageEdited",
        3: "EventUserJoined",
        4: "EventUserLeft",
        5: "EventRoomNameChanged",
        6: "EventMessageStarred",
        7: "EventDebugMessage",
        8: "EventUserMentioned",
        9: "EventMessageFlagged",
        10: "EventMessageDeleted",
        11: "EventFileAdded",
        12: "EventModeratorFlag",
        13: "EventUserSettingsChanged",
        14: "EventGlobalNotification",
        15: "EventAccessLevelChanged",
        16: "EventUserNotification",
        17: "EventInvitation",
        18: "EventMessageReply",
        19: "EventMessageMovedOut",
        20: "EventMessageMovedIn",
        21: "EventTimeBreak",
        22: "EventFeedTicker",
        29: "EventUserSuspended",
        30: "EventUserMerged",
        34: "EventUserNameOrAvatarChanged",
}


# useful functions
def log(msg, name="../logs/log.txt",verbose=True): # Logging messages and errors | Appends <msg> to the log <name>, prints if verbose
        msg=str(msg)
        with open(name, "ab") as f:
                timeStr = str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                f.write('{} {}\n'.format(timeStr,msg).encode('utf-8'))
                if verbose: print('<Log> {}'.format(msg.encode('utf-8')))

def logFile(r,name="../logs/logFile.html"):  # logs the string in the file <name>. Will overwrite previous data.
        with open(name, "wb") as f:
                f.write(r.encode('utf-8'))

def get_credidentials(decrypt_key = None): # gets credidentials from encrypted file / asks for them and encrypts them
        ## WARNING: ENCRYPTION DOES NOT SUPPORT PASSWORDS WITH " " (blank spaces) !!
        def pad(text): # makes length a multiple of 8 and transforms to bytes
                if len(text)%8==0: return text.encode('utf-8')
                return (text+' '*(8-len(text)%8) ).encode('utf-8')
        verif_text="verif||" # text used to check if the decrypted strings are the good ones, i.e. if the provided key is valid
        if os.path.isfile("Credidentials"): # Credidentials file exists, decrypt them
                goodPassword=False
                while not goodPassword:
                        if decrypt_key is None:
                                hash_password = pad(getpass.getpass("Password for the encrypted credidentials ? "))
                        else:
                                hash_password = pad(decrypt_key)
                        with open("Credidentials","rb") as f:
                                encrypted_string=f.read()
                        encrypted_verif=encrypted_string[:encrypted_string.find(b'/../')]
                        encrypted_email=encrypted_string[encrypted_string.find(b'/../')+len(b'/../'):encrypted_string.find(b'|..|')]
                        encrypted_password = encrypted_string[encrypted_string.find(b'|..|')+len(b'|..|'):]
                        key=Cryptodome.Cipher.DES.new(hash_password, Cryptodome.Cipher.DES.MODE_ECB)
                        try:
                                verif=key.decrypt(encrypted_verif)
                                email=(key.decrypt(encrypted_email)).replace(b' ',b'')
                                password=(key.decrypt(encrypted_password)).replace(b' ',b'')
                                goodPassword= verif==pad(verif_text)
                                if goodPassword:
                                        log('Credidentials retrieved successfully')
                        except Exception as e:
                                log('Error while decrypting credidentials: {}'.format(e))
                                goodPassword=False
                        if not goodPassword:
                                log('Bad password / corrupted file, try again.')
        else: # No credidentials are stored, ask for new ones
                email = str(input(("Email ? ")))  # SE email and passwords. Don't leave them as plain text.
                password = getpass.getpass("Password ? ")
                storeEncrypted=str(input("Do you want to encrypt and store those credidentials for a quicker access ? (y/n): ")).lower()
                if (storeEncrypted=='y' or storeEncrypted=='yes' or storeEncrypted is None or storeEncrypted==""):
                        goodPassword=False
                        hash_password1 = ""
                        while not goodPassword:
                                hash_password1 = getpass.getpass("Input a password to decrypt the credidentials : ")
                                hash_password2 = getpass.getpass("Confirmation - re-enter the password : ")
                                if hash_password1==hash_password2:
                                        goodPassword=True
                                else:
                                        log("The password do not match, try again.")
                        hash_password1=pad(hash_password1)
                        email=pad(email)
                        password=pad(password)
                        key=Cryptodome.Cipher.DES.new(hash_password1, Cryptodome.Cipher.DES.MODE_ECB)
                        encrypted_email = key.encrypt(email)
                        encrypted_password = key.encrypt(password)
                        encrypted_verif = key.encrypt(pad(verif_text))
                        with open("Credidentials","wb") as f:
                                f.write(encrypted_verif+b'/../'+encrypted_email+b'|..|'+encrypted_password)
                        log("Credidentials stored !")
        return email, password

def abort(): sys.exit()

# handle rooms interactions
class Room():
        def __init__(self, room_id, chatbot, onActivity):
                # propagate vars
                self.id=room_id # room identifier
                self.chatbot=chatbot # parent chatbot
                self.onActivity=onActivity # callback for events

                #initialize vars
                self.thread=None # own thread
                self.running=False # currently running ?
                self.ws=None # WebSocket
                self.temp_path="{}/temp".format(self.id)

                # initialize
                self.connect_ws() # attempt to connect via WebSockets
                if not os.path.exists("{}".format(self.id)):
                        os.makedirs("{}".format(self.id))
                if not os.path.exists("{}/temp".format(self.id)):
                        os.makedirs("{}/temp".format(self.id))

        def __repr__(self):
                return 'Room(id = {})'.format(self.id)

        def connect_ws(self):
                payload={"fkey": self.chatbot.fkey,'roomid': self.id}
                try:
                        print(self.chatbot.sendRequest("https://chat.stackexchange.com/ws-auth","post",payload).text)
                        r=json.loads(self.chatbot.sendRequest("https://chat.stackexchange.com/ws-auth","post",payload).text)
                except Exception as e:
                        log("Connection to room {} failed : {}".format(self.id,e))
                wsurl=r['url']+'?l={}'.format(int(time.time()))
                self.ws = websocket.create_connection(wsurl, origin="http://chat.stackexchange.com")
                self.thread = threading.Thread(target=self.run)
                #self.thread.setDaemon(True)
                self.thread.start()

        def run(self):
                self.running=True
                while self.running:
                        try:
                                a = self.ws.recv()
                        except:
                                log('Unexpected error for room {}; rebooting'.format(self.id))
                                raise SystemExit
                                self.running=False
                        if a is not None and a != "":# not an empty messages
                                a=json.loads(a)
                                if "r{}".format(self.id) in a:
                                        a=a["r{}".format(self.id)]
                                        if a!={}:
                                                try:
                                                        self.handleActivity(a)
                                                except:
                                                        pass

        def leave(self):
                log("Left room {}".format(self.id))
                self.running=False
                self.chatbot.rooms_joined.remove(self)

        def handleActivity(self, activity):
                log('Got activity {}'.format(activity), verbose=False)
                self.onActivity(activity)
                try: activity_timestamp=activity['t']
                except: log('Put in timeout for {} more seconds'.format(activity['timeout']))
                if "e" in activity: # if there are events recorded
                        for event in activity['e']:
                                if event['event_type'] > 2:
                                        log('Event: ' + EVENTS[event['event_type']])
                                        log('Event details: ' + str(event))

        def sendMessage(self, msg, wait=False):
                if not wait: log(msg)
                payload = {"fkey": self.chatbot.fkey, "text": msg}
                headers={'Referer': 'https://chat.stackexchange.com/rooms/{}'.format(self.id),'Origin': 'https://chat.stackexchange.com'}
                r = self.chatbot.sendRequest("http://chat.stackexchange.com/chats/{}/messages/new".format(self.id), "post", payload, headers=headers)
                if r.text.find("You can perform this action again") >= 0: # sending messages too fast
                        time.sleep(3)
                        return self.sendMessage(msg, True)
                if r.text.find("The message is too long") >= 0:
                        log("Message too long : {}".format(msg))
                        return False
                r = r.json()
                # log(r)
                return r["id"]

        def editMessage(self, msg, msg_id): # edit message with id <msg_id> to have the new content <msg>
                payload = {"fkey": self.chatbot.fkey, "text": msg}
                headers = {'Referer': "http://chat.stackexchange.com/rooms/{}".format(self.id)}
                r = self.chatbot.sendRequest("http://chat.stackexchange.com/messages/{}".format(msg_id), "post", payload, headers).text
                if r.find("You can perform this action again") >= 0:
                        time.sleep(3)
                        self.editMessage(msg, msg_id)

        def deleteMessage(self, msg_id): # delete message with id <msg_id>
                payload = {"fkey": self.chatbot.fkey}
                headers = {'Referer': "http://chat.stackexchange.com/rooms/{}".format(self.id)}
                r = self.chatbot.sendRequest("http://chat.stackexchange.com/messages/{}/delete".format(msg_id), "post", payload, headers).text
                if r.find("You can perform this action again") >= 0:
                        time.sleep(3)
                        self.deleteMessage(msg_id)

# main class
class Chatbot():
        def __init__(self, decrypt = None, verbose=True):
                # init vars
                self.session = requests.Session() # Session for POST/GET requests
                self.fkey=None # key used by SE to authentify users, needed to talk in the chat
                self.bot_chat_id=None
                self.rooms_joined=[]
                self.host=None
                self.decrypt_key = decrypt

                # propagate vars
                self.verbose=verbose

        def sendRequest(self, url, typeR="get", payload={}, headers={},verify=True): # sends a POST/GET request to <url> with arguments <payload>, headers <headers>. Will check SSL if <verify>.
                r = ""
                successful, tries = False, 0
                while not successful:
                        try:
                                if typeR == "get":
                                        r = self.session.get(url, data=payload, headers=headers, verify=verify)
                                elif typeR == "post":
                                        r = self.session.post(url, data=payload, headers=headers, verify=verify, cookies=requests.utils.dict_from_cookiejar(self.session.cookies)) # ugly patch
                                else:
                                        log("Error while sending requets -  Invalid request type :{}".format(typeR))
                                successful = True
                        except Exception as e:
                                time.sleep(1)
                                if tries >= 4:
                                        if type(r) != type(""):  # string or request object ?
                                                r = r.text
                                        log("Error while sending request - The request failed : {}".format(e))
                                        return False
                                tries += 1
                return r

        def log(self, msg, name="../logs/log.txt"): # Logging messages and errors | Appends <msg> to the log <name>, prints if self.verbose
                log(msg,name,verbose=self.verbose)

        def login(self, host="codegolf.stackexchange.com"): # Login to SE
                def getField(field, url="", r=""):
                        """gets the hidden field <field> from string <r> ELSE url <url>"""
                        if r == "":
                                r = self.sendRequest(url, 'get').text
                                r.encode('utf-8')
                        p = r.find('name="' + field)
                        if p <= 0:
                                error("No field <" + field + "> found", r)
                        p = r.find('value="', p) + len('value="')
                        key = r[p:r.find('"', p + 1)]
                        return key
                self.log("--- NEW LOGIN ---")

                email, password = get_credidentials(self.decrypt_key)

                # Login to OpenId / CSE
                fkey=getField("fkey", "https://openid.stackexchange.com/account/login")
                payload = {"email": email, "password": password, "isSignup":"false", "isLogin":"true","isPassword":"false","isAddLogin":"false","hasCaptcha":"false","ssrc":"head","submitButton":"Log in",
                           "fkey": fkey}
                r = self.sendRequest("https://{}/users/login-or-signup/validation/track".format(host),"post",payload).text
                if r.find("Login-OK")<0:
                        log("Logging to SE - FAILURE - aborting")
                        abort()
                log("Logging to SE - OK")

                payload = {"email": email, "password": password, "ssrc":"head", "fkey": fkey}
                r = self.sendRequest("https://{}/users/login?ssrc=head&returnurl=https%3a%2f%2f{}%2f".format(host, host),"post",payload).text
                if r.find('<a href="https://{}/users/logout"'.format(host))<0:
                        if 'Human verification' in r:
                                log('Caught by CAPTCHA')
                        log("Loading SE profile - FAILURE -  aborting")
                        abort()
                log("Loading SE profile - OK")

                # Logs in to all other SE sites
                self.sendRequest("https://{}/users/login/universal/request".format(host),"post")

                # get chat key
                r = self.sendRequest("https://chat.stackexchange.com/chats/join/favorite", "get").text
                p=r.find('<a href="/users/')+len('<a href="/users/')
                self.bot_chat_id=int(r[p:r.find('/',p)])
                fkey=getField("fkey", r=r) # /!\ changes from previous one
                self.fkey=fkey
                log("Got chat fkey : {}".format(fkey))
                log("Login to the SE chat successful")

        def joinRoom(self,room_id,onActivity): # Join a chatroom
                r=Room(room_id, self, onActivity)
                self.rooms_joined.append(r)
                return r

        def leaveAllRooms(self):
                for room in self.rooms_joined:
                        room.leave()

        def logout(self):
                self.sendRequest('https://openid.stackexchange.com/account/logout', 'post')
