import hmac, json, requests, yaml

from flask import request

def str_equals(x, y):
    if len(x) != len(y):
        return False
    result = 0
    for a, b in zip(x, y):
        result |= ord(a) ^ ord(b)
    return result == 0

with open("../configurations/vybot.txt", "rb") as f:
    secret = f.read().strip()

with open("data.yml", "r") as f:
    variables = yaml.safe_load(f)

with open("../configurations/vybot.json", "r") as f:
    STORAGE = json.load(f)

def save():
    with open("../configurations/vybot.json", "w") as f:
        f.write(json.dumps(STORAGE))

def send(message, **data):
    requests.post("http://localhost:5888", headers = {"Content-Type": "application/json"}, json = {
        "message": message,
        **data
    })

def link_user(user):
    if user == "github-actions[bot]":
        return f"The GitHub Actions bot"
    return f"[{user}](https://github.com/{user})"

def link_ref(refname, data):
    return f"[{data['repository']['name']}/{refname}]({data['repository']['url']}/tree/{refname})"

def link_issue(issue, caps = True):
    return f"[{'iI'[caps]}ssue #{issue['number']}]({issue['html_url']})"

def link_repository(repo, full_name = True):
    return f"[{repo['full_name' if full_name else 'name']}]({repo['html_url']})"

def msgify(text):
    return text.split("\n")[0].split("\r\f")[0].replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")

def execute(flags, code, inputs, header = "", footer = ""):
    if isinstance(inputs, (list, tuple)): inputs = "\n".join(inputs)

    payload = {
        "flags": flags,
        "code": code,
        "inputs": inputs,
        "header": header,
        "footer": footer
    }

    session = requests.Session()

    r = session.get("https://lyxal.pythonanywhere.com")
    if r.status_code == 200:
        start = r.text.find("<session-code>")
        end = r.text.find("</session-code>")
        if start == -1 or end == -1:
            return ("", "[GET /] returned 200 but the session code could not be located")
        payload["session"] = r.text[start + 14 : end]
    else:
        return ("", f"[GET /] returned {r.status_code}")

    r = session.post("https://lyxal.pythonanywhere.com/execute", data = payload)
    if r.status_code == 200:
        try:
            data = r.json()
            return (data["stdout"], data["stderr"])
        except:
            return ("", "[POST /execute] returned 200 but the output could not be parsed")
    else:
        return ("", f"[POST /execute] returned {r.status_code}")

def webhook(view):
    def inner(*a, **k):
        if not str_equals(request.headers.get("X-Hub-Signature-256", ""), "sha256=" + "".join(hex(byte)[2:].zfill(2) for byte in hmac.digest(secret, request.data, "sha256"))):
            return "", 201
        return view(request.json, *a, **k)
    inner.__name__ = view.__name__
    return inner

def msghook(view):
    def inner(*a, **k):
        data = request.json
        if data is None or data.get("secret") != secret.decode("utf-8"):
            return "", 201
        return view(*a, **k)
    inner.__name__ = view.__name__
    return inner
