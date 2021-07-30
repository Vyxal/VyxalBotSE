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
        return "@" + data["data"]["user_name"].replace(" ", "") + WELCOME
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
                        "@" + x.replace(" ", "")
                        for x in sorted(set(STORAGE["pings"]))
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
                return f"{reply} you are not a privileged user; ask someone if you believe you should be (user id: {message['user_id']})"
        if re.match(r"^pull$", without_ping):
            if message["user_id"] in STORAGE["admin"]:
                send(
                    f"{reply} pulling new changes; I will restart in a few seconds if any updates are available"
                )
                os.system("git pull")
                return ""
            else:
                return f"{reply} you are not an admin!"
        if re.match(r"^blame$", without_ping):
            return f"{reply} It was {random.choice(list({'wasif', 'Underslash', 'math', 'Aaron Miller', 'A username', 'user', 'Unrelated String', 'AviFS', 'Razetime', 'lyxal', '2x-1', 'hyper-neutrino'} - {message['user_name']}))}'s fault!"
        if re.match(r"^(hello|howdy|mornin['g]|evenin['g])$", without_ping):
            return f"{reply} hello to you too!"
        if re.match(r"^((good)?bye|see ya\!?|'night|goodnight)$", without_ping):
            return f"{reply} o/"
        if re.match(r"^flowey quote$", without_ping):
            return f"{reply} %s" % random.choice(
                [
                    "Howdy, I'm FLOWEY. FLOWEY the FLOWER",
                    "In this world, it's KILL or BE killed.",
                    "Hehehe, you really ARE an idiot.",
                    "Clever...verrrry clever. You think you're really smart, don't you.",
                    "Is this a joke? Are you braindead? RUN INTO THE BULLETS!!!",
                    "I've read every book. I've burned every book. I've won every game. I've lost every game. I've appeased everyone. I've killed everyone. Sets of numbers... Lines of dialog... I've seen them all.",
                    "You...! I'll keep you here no matter what! _Even if it means killing you 1,000,000 times!_",
                    "Down here, LOVE is shared through little white... 'friendliness pellets'",
                    "Hehehe... did you REALLY think you could defeat ME?",
                    "Don't you have anything better to do?",
                    "You! You're hopeless! Hopeless and _alone_",
                    "Don't you get it? This is all just a game... if you leave the underground satisfied, you'll \"WIN\" the game. And if you win, you won't want to play with me anymore",
                    "Why...why are you being so NICE to me?!? I can't understand. I just _can't_ understand",
                    "Hmmm, you're new to the underground, aren'tch'a? Golly, you must be so confused. Someone ought to teach you how things work around here",
                    "What's LV stand for? Why LOVE of course! You want some LOVE don't you? Don't worry, I'll share some with you!",
                    "You IDIOT!",
                    "Why would anyone pass up an opportunity like this? DIE!",
                    "So you were able to play by your own rules. You spared the life of a single person. Hee hee hee... I bet you feel really great.",
                    "Don't worry, my little monarch, my plan isn't regicide...this is SO much more interesting.",
                    "You idiot. You haven't learned a thing. In this world...**I T S  K I L L  O R  B E  K I L L E D**",
                    "No...NO! This can't be happening! You...YOU! _You IDIOT!_",
                    "I owe you a HUGE thanks...you really did a number on that old fool. Without you, I NEVER could have gotten past him",
                    "What? Do you really think you can stop ME? Hee hee hee...you really ARE an idiot.",
                    "Boy! What a shame! Nobody else...is going to get to see you DIE!!!",
                    "What?! How'd you...?! Well I'll just. Wh...where are my powers?! The souls...? What are they doing? NO!! NO!!!!! YOU CAN'T DO THAT!!! YOU'RE SUPPOSED TO OBEY ME!! STOP!!! STOP IT!!!!! STOOOOPPPP!!!!!",
                    "...What are you doing? Do you really think I've learned anything from this? No. Sparing me won't change anything.",
                    "And you know what the best part is? This is all YOUR fault!",
                    "Let's destroy everything in this wretched world. Everyone, everything in these worthless memories... Let's turn 'em all to dust.",
                    "_that's a wonderful idea!_",
                    'At first, I used my powers for good. I became "friends" with everyone. I solved all their problems flawlessly. Their companionship was amusing... For a while.',
                    "It doesn't matter now. I'm so tired of this, Chara. I'm tired of all these people. I'm tired of all these places. I'm tired of being a flower.",
                ]
            )
        if re.match(r"^hug$", without_ping):
            return f"{reply} %s" % random.choice(
                [
                    "⊂((・▽・))⊃",
                    "⊂(◉‿◉)つ",
                    "(づ｡◕‿‿◕｡)づ",
                    "༼ つ ◕_◕ ༽つ",
                    "(つ ͡° ͜ʖ ͡°)つ",
                    "༼ つ ◕o◕ ༽つ",
                ]
            )
        if re.match(r"^sus$", without_ping):
            return f"{reply} ඞ"
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
                return f"{reply} failed to fetch repositories; if this persists, submit an issue"
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
