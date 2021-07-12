import requests

payload = {
  "flags": "H",
  "code": "++",
  "inputs": "1\n2",
  "header": "",
  "footer": ""
}

session = requests.Session()

r = session.get("https://lyxal.pythonanywhere.com")

ssid = r.text[r.text.find("<session-code>") + 14:r.text.find("</session-code>")]

payload["session"] = ssid

r = session.post("https://lyxal.pythonanywhere.com/execute", data = payload)

print(r.json())