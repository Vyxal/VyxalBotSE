import json

from main import app
from utils import *
from variables import *


@app.route("/branch-tag-created", methods=["POST"])
@webhook
def webhook_branch_tag_created(data):
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
    if data["ref_type"] == "branch":
        send(
            link_user(data["sender"]["login"])
            + " deleted branch "
            + data["repository"]["name"]
            + "/"
            + data["ref"]
        )
    return ""


@app.route("/discussion", methods=["POST"])
@webhook
def webhook_discussion(data):
    action = data["action"]
    if action == "created":
        send(
            link_user(data["sender"]["login"])
            + " created a discussion in "
            + link_repository(data["repository"])
            + ": "
            + link_discussion(data["discussion"])
        )
    elif action == "deleted":
        send(
            link_user(data["sender"]["login"])
            + " deleted a discussion in "
            + link_repository(data["repository"])
            + ": "
            + data["discussion"]["title"]
        )
    elif action == "pinned":
        send(
            link_user(data["sender"]["login"])
            + " pinned a discussion in "
            + link_repository(data["repository"])
            + ": "
            + link_discussion(data["discussion"])
        )
    return ""


@app.route("/fork", methods=["POST"])
@webhook
def webhook_fork(data):
    send(
        link_user(data["sender"]["login"])
        + " forked "
        + link_repository(data["repository"])
        + " into "
        + link_repository(data["forkee"])
    )
    return ""


@app.route("/issue", methods=["POST"])
@webhook
def webhook_issue(data):
    action = data["action"]
    if action == "opened":
        send(
            link_user(data["sender"]["login"])
            + " opened "
            + link_issue(data["issue"], caps=False)
            + " in "
            + link_repository(data["repository"])
            + ": _"
            + msgify(data["issue"]["title"])
            + "_"
        )
    elif action in ["deleted", "closed", "edited", "reopened"]:
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
            + link_repository(data["repository"])
            + ")"
        )
    return ""


@app.route("/pr-review-comment", methods=["POST"])
@webhook
def webhook_pr_review_comment(data):
    if data["action"] == "created":
        send(
            link_user(data["sender"]["login"])
            + " [commented]("
            + data["comment"]["url"]
            + ") on "
            + link_pull_request(data["pull_request"])
            + " in file `"
            + data["comment"]["path"]
            + '`: "'
            + msgify(data["comment"]["body"])
            + '"'
        )
    return ""


@app.route("/pr-review", methods=["POST"])
@webhook
def webhook_pr_review(data):
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
    if action == "opened":
        action_text = "opened"
    elif action == "closed":
        if data.get("merged"):
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
    return ""


@app.route("/push", methods=["POST"])
@webhook
def webhook_push(data):
    commits = data["commits"]
    if len(commits) == 0:
        return ""
    commit = commits[-1]
    if len(commits) == 1:
        send(
            link_user(data["sender"]["login"])
            + " pushed a [commit]("
            + commit["url"]
            + ") to "
            + link_ref(data["ref"][11:], data)
            + ": "
            + msgify(commit["message"])
        )
    else:
        send(
            link_user(data["sender"]["login"])
            + " pushed "
            + str(len(commits))
            + " commits to "
            + link_ref(data["ref"][11:], data)
            + ". [Last commit]("
            + commits[-1]["url"]
            + "): "
            + msgify(commit["message"])
        )
    return ""


@app.route("/release", methods=["POST"])
@webhook
def webhook_release(data):
    release = data["release"]
    repository = data["repository"]
    primary = repository["full_name"] == "Vyxal/Vyxal"
    send(
        "[**"
        + (release["name"] or release["tag_name"])
        + "**]("
        + release["html_url"]
        + ")"
        + ("" if primary else " released in " + link_repository(repository)),
        pin=primary,
    )
    return ""


@app.route("/repository", methods=["POST"])
@webhook
def webhook_repository(data):
    data = request.json
    action = data["action"]
    repository = data["repository"]
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
        if repo["full_name"] == "Vyxal/Vyxal":
            send(PRIMARY_ARCHIVED)
    elif action == "unarchived":
        pass
    elif action == "publicized":
        pass
    elif action == "privatized":
        if repo["full_name"] == "Vyxal/Vyxal":
            send(PRIMARY_PRIVATIZED)
    else:
        return ""
    send(link_user(user) + " " + action + " " + link_repository(repository))
    return ""


@app.route("/vulnerability", methods=["POST"])
@webhook
def webhook_vulnerability(data):
    alert = data["alert"]
    send(
        "**"
        + alert["severity"]
        + " created by "
        + link_user(data["sender"]["login"])
        + " in "
        + link_repository(data["repository"])
        + " (affected package: _"
        + msgify(alert["affected_package_name"])
        + " "
        + alert["affected_range"]
        + "_)"
    )
    return ""
