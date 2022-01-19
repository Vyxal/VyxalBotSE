import html
import re
import traceback

from chatbot import *

rid = 240


def execute(flags, code, inputs, header="", footer=""):
    if isinstance(inputs, (list, tuple)):
        inputs = "\n".join(inputs)

    payload = {
        "flags": flags,
        "code": code,
        "inputs": inputs,
        "header": header,
        "footer": footer,
    }

    session = requests.Session()

    r = session.get("https://vyxal.pythonanywhere.com")
    if r.status_code == 200:
        start = r.text.find("<session-code>")
        end = r.text.find("</session-code>")
        if start == -1 or end == -1:
            return (
                "",
                "[GET /] returned 200 but the session code "
                "could not be located",
            )
        payload["session"] = r.text[start + 14 : end]
    else:
        return ("", f"[GET /] returned {r.status_code}")

    r = session.post("https://vyxal.pythonanywhere.com/execute", data=payload)
    if r.status_code == 200:
        try:
            data = r.json()
            return (data["stdout"], data["stderr"])
        except:
            return (
                "",
                "[POST /execute] returned 200 but the output "
                "could not be parsed",
            )
    else:
        return ("", f"[POST /execute] returned {r.status_code}")


ignored = set()
owners = {281362, 354515, 218449, 274572, 322760, 347075, 130368, 337270}


def response(x):
    try:
        content = html.unescape(x["content"])
        reply = ":" + str(x["message_id"]) + " "
        runhelp = "`!!/run \`code\` \`flags (- to exclude)\` \`input line\` \`input line\` ...`"
        if content == "!!/info":
            return (
                reply
                + "[GitHub Repository](https://github.com/Vyxal/Vyxal/) | "
                + "[Online Interpreter](https://vyxal.pythonanywhere.com) | "
                + "[Tutorial](https://github.com/Vyxal/Vyxal/blob/master/docs/Tutorial.md) | "
                + "[Vyxapedia](https://vyxapedia.hyper-neutrino.xyz) | "
                + "[List of elements](https://github.com/Vyxal/Vyxal/blob/main/documents/knowledge/elements.md) | "
                + "[Code Page](https://github.com/Vyxal/Vyxal/blob/master/docs/codepage.txt) | "
                + "[GitHub Organization](https://github.com/Vyxal/)"
            )
        if content == "!!/run" or content == "!!/help":
            return reply + runhelp
        if content == "!!/status":
            return reply + "I am running fine!"
        if content.startswith("!!/ignore "):
            if x["user_id"] in owners:
                ignored.add(int(content[10:]))
            return
        if content.startswith("!!/unignore "):
            if x["user_id"] in owners:
                ignored.discard(int(content[12:]))
            return
        if content.startswith("!!/run "):
            content = content[7:]
            if not re.match("^(<code>(.*?)</code>\\s*)+$", content):
                return reply + runhelp
            data = re.findall("<code>(.*?)</code>", content)
            if len(data) == 1:
                code, flags, inputs = data[0], "", []
            else:
                code, flags, *inputs = data
            if code == "lyxal":
                return reply + "https://youtube.com/watch?v=dQw4w9WgXcQ"
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
                    + x["user_name"].replace(" ", "")
                    + ": "
                    + str(x["message_id"])
                    + "]",
                )
                return "\n".join("    " + line for line in output)
    except:
        traceback.print_exc()


def handler(activity):
    if "e" in activity:
        for x in activity["e"]:
            if x.get("room_id") != rid:
                continue
            if x.get("user_id") in ignored | {296403} - owners:
                continue
            id = x.get("message_id")
            et = x["event_type"]
            if et == 1:
                r = response(x)
                if r:
                    links[id] = room.sendMessage(r)
            elif et == 2:
                r = response(x)
                if r:
                    room.editMessage(r, links[id])
                elif id in links:
                    room.editMessage(
                        "(message response failed or the new message is not a "
                        "command)",
                        links[id],
                    )
            elif et == 10:
                if id in links:
                    room.deleteMessage(links[id])
                    del links[id]


chatbot = Chatbot()
chatbot.login()

room = chatbot.joinRoom(rid, handler)
links = {}
