import json
import re

from main import app
from utils import *
from variables import *

config = json.loads(open("config.json", "r").read())
token = config["github_token"]

def git_request(url, options):
    headers = {
        "Authorization": "token " + token,
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Vyxal-Bot",
    }
    headers.update(options.get("headers", {}))
    options["headers"] = headers

    response = requests.request("https://api.github.com" + url, **options)
    return response


@app.route("/branch-tag-created", methods=["POST"])
@webhook
def webhook_branch_tag_created(data):
    repository = data["repository"]
    if repository["private"]:
        return ""
    if data["ref_type"] == "branch":
        send(
            link_user(data["sender"]["login"])
            + " created branch "
            + link_ref(data["ref"], data)
        )
    return ""


@app.route("/branch-tag-deleted", methods=["POST"])
@webhook
def webhook_branch_tag_deleted(data):
    repository = data["repository"]
    if repository["private"]:
        return ""
    if data["ref_type"] == "branch":
        send(
            link_user(data["sender"]["login"])
            + " deleted branch "
            + repository["name"]
            + "/"
            + data["ref"]
        )
    return ""


@app.route("/discussion", methods=["POST"])
@webhook
def webhook_discussion(data):
    repository = data["repository"]
    if repository["private"]:
        return ""
    action = data["action"]
    if action == "created":
        send(
            link_user(data["sender"]["login"])
            + " created a discussion in "
            + link_repository(repository)
            + ": "
            + link_discussion(data["discussion"])
        )
    elif action == "deleted":
        send(
            link_user(data["sender"]["login"])
            + " deleted a discussion in "
            + link_repository(repository)
            + ": "
            + data["discussion"]["title"]
        )
    elif action == "pinned":
        send(
            link_user(data["sender"]["login"])
            + " pinned a discussion in "
            + link_repository(repository)
            + ": "
            + link_discussion(data["discussion"])
        )
    return ""


@app.route("/fork", methods=["POST"])
@webhook
def webhook_fork(data):
    repository = data["repository"]
    if repository["private"]:
        return ""
    send(
        link_user(data["sender"]["login"])
        + " forked "
        + link_repository(repository)
        + " into "
        + link_repository(data["forkee"])
    )
    return ""


@app.route("/issue", methods=["POST"])
@webhook
def webhook_issue(data):
    repository = data["repository"]
    if repository["private"]:
        return ""
    action = data["action"]
    if action == "opened":
        send(
            link_user(data["sender"]["login"])
            + " opened "
            + link_issue(data["issue"], caps=False)
            + " in "
            + link_repository(repository)
            + ": _"
            + msgify(data["issue"]["title"])
            + "_"
        )
    elif action in ["deleted", "closed", "reopened"]:  # removed "edited"
        issue_link = (
            "issue #" + str(data["issue"]["number"])
            if action == "deleted"
            else link_issue(data["issue"], caps=False)
        )
        send(
            link_user(data["sender"]["login"])
            + " "
            + action
            + " "
            + issue_link
            + " (_"
            + msgify(data["issue"]["title"])
            + "_, "
            + link_repository(repository)
            + ")"
        )
    return ""


@app.route("/pr-review-comment", methods=["POST"])
@webhook
def webhook_pr_review_comment(data):
    # if data["action"] == "created":
    #     send(
    #         link_user(data["sender"]["login"])
    #         + " [commented]("
    #         + data["comment"]["html_url"]
    #         + ") on "
    #         + link_pull_request(data["pull_request"])
    #         + " in file `"
    #         + data["comment"]["path"]
    #         + '`: "'
    #         + msgify(data["comment"]["body"])
    #         + '"'
    #     )
    return ""


@app.route("/pr-review", methods=["POST"])
@webhook
def webhook_pr_review(data):
    if data["repository"]["private"]:
        return ""
    if data["action"] == "submitted":
        review = data["review"]
        if review["state"] == "commented":
            if not review["body"]:
                return ""
            action_text = "commented"
        elif review["state"] == "approved":
            action_text = "approved"
        elif review["state"] == "changes_requested":
            action_text = "requested changes"
        else:
            return ""
        send(
            link_user(data["sender"]["login"])
            + " ["
            + action_text
            + "]("
            + review["html_url"]
            + ") on "
            + link_pull_request(data["pull_request"])
            + (': "' + msgify(review["body"]) + '"' if review["body"] else "")
        )
    return ""


@app.route("/pull-request", methods=["POST"])
@webhook
def webhook_pull_request(data):
    action = data["action"]
    pr = data["pull_request"]
    if pr["head"]["repo"]["private"]:
        return ""
    if action == "opened":
        action_text = "opened"
    elif action == "closed":
        if pr.get("merged_at"):
            action_text = "merged"
        else:
            action_text = "closed"
    elif action == "reopened":
        action_text = "reopened"
    else:
        return ""
    send(
        link_user(data["sender"]["login"])
        + " "
        + action_text
        + " "
        + link_pull_request(pr)
        + " ("
        + pr["head"]["label"]
        + " → "
        + pr["base"]["label"]
        + ")"
        + ": _"
        + msgify(pr["title"])
        + "_"
    )
    if action == "opened":
        # Perform autolabelling of issues
        # ported form the JS I wrote originally

        if pr["base"]["repo"]["full_name"] != "Vyxal/Vyxal":
            # Only PRs on the main repo are autolabelled
            return ""

        if len(pr["labels"]) > 0:
            # Don't label something that already has labels
            return ""

        pr_body = pr["body"]
        if not pr_body:
            return ""

        # If we get here, we know that the PR might have an issue linked to it.
        # We can now get the issue number.

        issue_pobj = re.compile(r"([Cc]lose[sd]?|[Ff]ixe[sd]) #(\d+)/")
        contains_issue = issue_pobj.match(pr_body)
        if not contains_issue:
            return ""

        issue_number = contains_issue.group(2)
        subres = git_request(
            f"/repos/{pr['base']['repo.full_name']}/issues/{issue_number}",
            {
                "method": "GET",
            },
        )

        if subres.status_code != 200:
            return ""

        issue = subres.json()
        labels = issue["labels"]

        if len(labels) == 0:
            return ""

        label_names = []
        for label in labels:
            label_names.append(label["name"])

        def map_label(label):
            if label == "bug":
                return "PR: Bug Fix"
            elif label == "documentation":
                return "PR: Documentation Fix"
            elif label == "request: element":
                return "PR: Element Implementation"
            elif label == "enhancement":
                return "PR: Enhancement"
            elif label == "difficulty: very hard":
                return "PR: Careful Review Required"
            elif label == "priority: high":
                return "PR: Urgent Review Required"
            elif label == "online interpreter":
                return "PR: Online Interpreter"
            elif label == "version-3":
                return "PR: Version 3 Related"
            elif label in ["difficulty: easy", "good first issue"]:
                return "PR: Light and Easy"
            else:
                return ""

        label_names = list(map(map_label, label_names))
        # Keep only non-empty strings
        label_names = list(filter(lambda x: x, label_names))

        if label_names:
            options = {
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                },
                "data": json.dumps({"labels": label_names}),
            }
            url = f"/repos/{pr['base']['repo']['full_name']}/issues/{pr['number']}/labels"
            git_request(url, options)

    return ""


@app.route("/push", methods=["POST"])
@webhook
def webhook_push(data):
    # commits = data["commits"]
    # if len(commits) == 0:
    #     return ""
    # commit = commits[-1]
    # if len(commits) == 1:
    #     send(
    #         link_user(data["sender"]["login"])
    #         + " pushed a [commit]("
    #         + commit["url"]
    #         + ") to "
    #         + link_ref(data["ref"][11:], data)
    #         + ": "
    #         + msgify(commit["message"])
    #     )
    # else:
    #     send(
    #         link_user(data["sender"]["login"])
    #         + " pushed "
    #         + str(len(commits))
    #         + " commits to "
    #         + link_ref(data["ref"][11:], data)
    #         + ". [Last commit]("
    #         + commits[-1]["url"]
    #         + "): "
    #         + msgify(commit["message"])
    #     )
    return ""


last_release = None

primary = {"Vyxal/Vyxal"}
secondary = primary | {"Vyxal/Jyxal"}


@app.route("/release", methods=["POST"])
@webhook
def webhook_release(data):
    global last_release
    release = data["release"]
    if release == last_release:
        return
    last_release = release
    repository = data["repository"]
    if repository["private"]:
        return ""
    name = repository["full_name"]
    send(
        "[**"
        + (release["name"] or release["tag_name"])
        + "**]("
        + release["html_url"]
        + ")"
        + (
            ""
            if name in secondary
            else " released in " + link_repository(repository)
        ),
        pin=name in primary,
    )
    return ""


@app.route("/repository", methods=["POST"])
@webhook
def webhook_repository(data):
    data = request.json
    action = data["action"]
    repository = data["repository"]
    if repository["private"]:
        return ""
    user = data["sender"]["login"]
    if action == "created":
        send(
            link_user(user)
            + " created a repository: "
            + link_repository(repository)
        )
        return ""
    elif action == "deleted":
        send(
            link_user(user)
            + " deleted a repository: "
            + repository["full_name"]
        )
        if repository["full_name"] == "Vyxal/Vyxal":
            send(PRIMARY_DELETED)
        return ""
    elif action == "archived":
        if repository["full_name"] == "Vyxal/Vyxal":
            send(PRIMARY_ARCHIVED)
    elif action == "unarchived":
        pass
    elif action == "publicized":
        pass
    elif action == "privatized":
        if repository["full_name"] == "Vyxal/Vyxal":
            send(PRIMARY_PRIVATIZED)
    else:
        return ""
    send(link_user(user) + " " + action + " " + link_repository(repository))
    return ""


@app.route("/vulnerability", methods=["POST"])
@webhook
def webhook_vulnerability(data):
    repository = data["repository"]
    if repository["private"]:
        return ""
    alert = data["alert"]
    send(
        "**"
        + alert["severity"]
        + " created by "
        + link_user(data["sender"]["login"])
        + " in "
        + link_repository(repository)
        + " (affected package: _"
        + msgify(alert["affected_package_name"])
        + " "
        + alert["affected_range"]
        + "_)"
    )
    return ""
