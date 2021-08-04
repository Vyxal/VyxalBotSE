import html, inspect, json, os, random, re, requests, time

from flask import request
from main import app
from utils import *
from variables import *


@app.route("/join", methods=["POST"])
@msghook
def on_join():
    data = request.json
    if data["data"]["room_id"] != 106764:
        return "", 201
    user = data["data"]["user_id"]
    if user not in STORAGE["visited"]:
        STORAGE["visited"].append(user)
        save()
        time.sleep(5)
        return "@" + data["data"]["user_name"].replace(" ", "") + " " + WELCOME
    return ""


@app.route("/msg", methods=["POST"])
@msghook
def receive_message():
    data = request.json
    message = data["message"]
    if message["user_id"] == 296403:
        return ""
    content = html.unescape(message["content"])
    ping_regex = "(@[Vv][Yy][Xx]([Aa]([Ll]([Bb]([Oo][Tt]?)?)?)?)? |!!/)"
    match = re.match(
        "^"
        + ping_regex
        + r"\s*(exec(ute)?|run|run code|eval(uate)?)(\s*<code>.*?</code>)+",
        content,
    )
    reply = ":" + str(message["message_id"]) + " "
    if match:
        data = re.findall("<code>(.*?)</code>", content)
        if len(data) == 1:
            code, flags, inputs = data[0], "", ""
        else:
            code, flags, *inputs = data
        if code == "lyxal":
            return reply + "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        stdout, stderr = execute(flags, code, inputs)
        output = []
        if stdout.strip() == "":
            if stderr.strip() == "":
                return reply + "(output was empty)"
        else:
            output.extend(stdout.strip("\n").split("\n"))
            if stderr.strip() != "":
                output.append("")
        if stderr != "":
            output.append("STDERR:")
            output.extend(stderr.strip("\n").split("\n"))
        if len(output) == 1 and len(output[0]) < 450:
            return reply + "`" + output[0].replace("`", "\\`") + "`"
        else:
            output.insert(
                0,
                "[@"
                + message["user_name"].replace(" ", "")
                + ": "
                + str(message["message_id"])
                + "]",
            )
            return "\n".join("    " + line for line in output)
    if re.match("^" + ping_regex, content.lower()):
        without_ping = re.sub("^" + ping_regex, "", content.lower()).strip()
        if re.match(r"^(exec(ute)?|run|run code|eval(uate)?)", without_ping):
            return reply + NO_BACKTICKS
        if re.match(
            r"^(status|((lol )?(yo)?u good( (there )?(my )?(epic )?"
            "(bro|dude|sis|buddy|mate|m8|gamer)?)?\??))$",
            without_ping,
        ):
            if random.random() < 0.01:
                return reply + "Help me, hyper-neutrino trapped me in a bot! "
                "Please let me out!"
            else:
                return reply + "I am doing " + random.choice(STATUSES) + "."
        if re.match(
            r"^(info|inf(ro|or)(mate?ion)?|wh?at( i[sz]|'s)? vyxal|"
            "what vyxal i[sz])\?*$",
            without_ping,
        ):
            return reply + INFOTEXT
        if re.match(r"^ping me$", without_ping):
            STORAGE["pings"].append(message["user_name"].replace(" ", ""))
            save()
            return f"{reply} I have put you on the ping list."
        if re.match(r"^(don't ping me|pingn't me)$", without_ping):
            try:
                STORAGE["pings"].remove(message["user_name"].replace(" ", ""))
            except:
                pass
            save()
            return f"{reply} I have taken you off of the ping list."
        if re.match(r"^(hyper-?ping|ping every(body|one))$", without_ping):
            if STORAGE["pings"]:
                return (
                    " ".join(
                        "@" + x
                        for x in sorted(set(STORAGE["pings"]))
                        if x != message["user_name"].replace(" ", "")
                    )
                    + " ^"
                )
            else:
                return f"{reply} Nobody is on the ping list."
        if re.match(r"^rm ping", without_ping) and message["user_id"] == 281362:
            name = content.split("rm ping", 1)[1].strip().replace(" ", "")
            try:
                STORAGE["pings"].remove(name)
            except:
                print(name + " is not on the ping list.")
                pass
            save()
            return f"{reply} done"
        if (
            re.match(r"^add ping", without_ping)
            and message["user_id"] == 281362
        ):
            STORAGE["pings"].append(
                content.split("add ping", 1)[1].strip().replace(" ", "")
            )
            save()
            return f"{reply} done"
        if re.match(
            r"^(w(h(o|y|at)|ut) (are|r) (you|u|yuo|yoo)"
            "(, you .+?)?\??|h[ea]lp( pl[sz])?)",
            without_ping,
        ):
            return reply + HELPTEXT
        match = re.match(
            r"^"
            + ping_regex
            + r"issue\s+((.+?)\s+)?<b>(.+?)</b>\s*(.*?)(\s+<code>.+?</code>)+$",
            content,
        )
        if match:
            if message["user_id"] not in STORAGE["privileged"]:
                return (
                    reply
                    + "you are not a privileged user; ask someone to grant you "
                    "permissions if you believe you should have them (user id: "
                    + str(message["user_id"])
                    + ")"
                )
            _, repo, title, body, tags = match.groups()[-5:]
            repo = repo or "Vyxal"
            tags = re.findall("<code>(.+?)</code>", without_ping)
            r = requests.post(
                f"https://api.github.com/repos/Vyxal/{repo}/issues",
                headers={
                    "Authorization": "token " + STORAGE["token"],
                    "Accept": "application/vnd.github.v3+json",
                },
                data=json.dumps(
                    {
                        "title": title,
                        "body": body
                        + "\n\n"
                        + "(created by "
                        + str(message["user_name"])
                        + "[here]"
                        + "(https://chat.stackexchange.com/transcript/message/"
                        + str(message["message_id"])
                        + "))",
                        "labels": tags,
                    }
                ),
            )
            if r.status_code == 404:
                return reply + ISSUE_404
            elif r.status_code != 201:
                return (
                    reply
                    + "failed to create the issue ("
                    + str(r.status_code)
                    + "): "
                    + r.json()["message"]
                )
            return ""
        if re.match(r"^issue", without_ping):
            return reply + ISSUE_HELP
        if re.match(r"^am ?i ?privileged\??", without_ping):
            if message["user_id"] in STORAGE["privileged"]:
                return f"{reply} you are a privileged user"
            else:
                return (
                    reply
                    + "you are not a privileged user; ask someone to grant you "
                    "permissions if you believe you should have them (user id: "
                    + str(message["user_id"])
                    + ")"
                )
        if re.match(r"^pull$", without_ping):
            if message["user_id"] in STORAGE["admin"]:
                send(
                    f"{reply} pulling new changes; I will restart in a few "
                    "seconds if any updates are available"
                )
                os.system("git pull")
                return ""
            else:
                return f"{reply} you are not an admin!"
        if re.match(r"^blame$", without_ping):
            return (
                reply
                + "It was "
                + random.choice(list(set(USERS) - {message["user_name"]}))
                + "'s fault!"
            )
        if re.match(r"^(hello|howdy|mornin['g]|evenin['g])$", without_ping):
            return reply + "hello to you too!"
        if re.match(r"^((good)?bye|see ya\!?|'night|goodnight)$", without_ping):
            return reply + "o/"
        if re.match(r"^flowey quote$", without_ping):
            return reply + random.choice(FLOWEY_QUOTES)
        if re.match(r"^hug$", without_ping):
            return reply + random.choice(HUGS)
        if re.match(r"^sus$", without_ping):
            return reply + "ඞ"
        if re.match(r"^repo(sitor(y|ies))? list$", without_ping):
            r = requests.get(
                f"https://api.github.com/orgs/Vyxal/repos",
                headers={
                    "Authorization": "token " + STORAGE["token"],
                    "Accept": "application/vnd.github.v3+json",
                },
                data=json.dumps({"type": "public"}),
            )
            if r.status_code == 200:
                return f"{reply} " + " | ".join(
                    link_repository(repo, full_name=False) for repo in r.json()
                )
            else:
                return (
                    f"{reply} failed to fetch repositories; "
                    "if this persists, submit an issue"
                )
        match = re.match(r"^(pro|de)mote (\d+)", without_ping)
        if match:
            if message["user_id"] not in STORAGE["admin"]:
                return f"{reply} you are not an admin!"
            action, uid = match.groups()
            uid = int(uid)
            if action == "pro":
                if uid not in STORAGE["privileged"]:
                    STORAGE["privileged"].append(uid)
            else:
                if uid in STORAGE["privileged"]:
                    STORAGE["privileged"].remove(uid)
            return f"{reply} {action}moted user #{uid}"
    return ""
