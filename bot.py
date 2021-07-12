import html, json, re, requests, traceback

from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)

from chatbot import *

with open("../configurations/vybot.txt", "r") as f:
  secret = f.read().strip()

hooks = {}
  
def handler(room):
  def _inner(activity):
    if "e" in activity:
      for x in activity["e"]:
        if x["event_type"] == 1 and x["room_id"] == room:
          if x["user_id"] == 296403: return
          try:
            r = requests.post("http://localhost:5666/msg", headers = {"Content-Type": "application/json"}, json = {"secret": secret, "message": x})
            if r.status_code == 200 and r.text:
              hooks[x["message_id"]] = send(r.text)
          except:
            traceback.print_exc()
        elif x["event_type"] == 2 and x["room_id"] == room:
          if x["user_id"] == 296403: return
          try:
            r = requests.post("http://localhost:5666/msg", headers = {"Content-Type": "application/json"}, json = {"secret": secret, "message": x})
            if r.status_code == 200 and r.text:
              if x["message_id"] in hooks:
                rooms[rid].editMessage(r.text, hooks[x["message_id"]])
              else:
                hooks[x["message_id"]] = send(r.text)
          except:
            traceback.print_exc()
  return _inner

chatbot = Chatbot()
chatbot.login()

rid = 106764

rooms = {
  k: chatbot.joinRoom(k, handler(k)) for k in [rid]
}

def send(message):
  return rooms[rid].sendMessage(message)

@app.route("/", methods = ["POST"])
def post_message():
  data = request.json
  send(data["message"])
  return ""

if __name__ == "__main__":
  app.run(host = "localhost", port = 5888)