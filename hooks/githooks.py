import json

from main import app
from utils import *
from variables import *


@app.route("/branch-tag-created", methods=["POST"])
@webhook
def webhook_branch_tag_created(data):
    if data["ref_type"] == "branch":
        send(
            "Branch "
            + link_ref(data["ref"], data)
            + " was created by "
            + link_user(data["sender"]["login"])
        )
    return ""


@app.route("/branch-tag-deleted", methods=["POST"])
@webhook
def webhook_branch_tag_deleted(data):
    if data["ref_type"] == "branch":
        send(
            "Branch "
            + data["repository"]["name"]
            + "/"
            + data["ref"]
            + " was deleted by "
            + link_user(data["sender"]["login"])
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
            + data["comment"]["body"].split("\n")[0]
            + '"'
        )
    return ""


@app.route("/pr-review", methods=["POST"])
@webhook
def webhook_pr_review(data):
    if data["action"] == "submitted":
        review = data["review"]
        if review["state"] == "commented":
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
            + (
                ': "' + review["body"].split("\n")[0] + '"'
                if review["body"]
                else ""
            )
        )
    return ""


@app.route("/pull-request", methods=["POST"])
@webhook
def webhook_pull_request(data):
    return ""


@app.route("/push", methods=["POST"])
@webhook
def webhook_push(data):
    commits = data["commits"]
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
    elif len(commits) != 0:
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
    return ""


@app.route("/repository", methods=["POST"])
@webhook
def webhook_repository(data):
    return ""


@app.route("/vulnerability", methods=["POST"])
@webhook
def webhook_vulnerability(data):
    return ""
