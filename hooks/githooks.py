from main import app
from utils import *
from variables import *


@app.route("/branch-tag-created", methods=["POST"])
@webhook
def webhook_branch_tag_created(data):
    if data["ref_type"] == "branch":
        send(
            link_user(data["sender"]["login"])
            + " created a new branch: "
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
    return ""


@app.route("/fork", methods=["POST"])
@webhook
def webhook_fork(data):
    return ""


@app.route("/issue", methods=["POST"])
@webhook
def webhook_issue(data):
    return ""


@app.route("/organization", methods=["POST"])
@webhook
def webhook_organization(data):
    return ""


@app.route("/pr-review-comment", methods=["POST"])
@webhook
def webhook_pr_review_comment(data):
    return ""


@app.route("/pr-review-thread", methods=["POST"])
@webhook
def webhook_pr_review_thread(data):
    return ""


@app.route("/pr-review", methods=["POST"])
@webhook
def webhook_pr_review(data):
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
            + link_ref(data["ref"][11:], data)
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
