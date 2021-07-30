from main import app
from utils import *

@app.route("/branch-tag-created", methods = ["POST"])
@webhook
def webhook_branch_tag_created(data):
    return ""

@app.route("/branch-tag-deleted", methods = ["POST"])
@webhook
def webhook_branch_tag_deleted(data):
    return ""

@app.route("/discussion", methods = ["POST"])
@webhook
def webhook_discussion(data):
    return ""

@app.route("/fork", methods = ["POST"])
@webhook
def webhook_fork(data):
    return ""

@app.route("/issue", methods = ["POST"])
@webhook
def webhook_issue(data):
    return ""

@app.route("/organization", methods = ["POST"])
@webhook
def webhook_organization(data):
    return ""

@app.route("/pr-review-comment", methods = ["POST"])
@webhook
def webhook_pr_review_comment(data):
    return ""

@app.route("/pr-review-thread", methods = ["POST"])
@webhook
def webhook_pr_review_thread(data):
    return ""

@app.route("/pr-review", methods = ["POST"])
@webhook
def webhook_pr_review(data):
    return ""

@app.route("/pull-request", methods = ["POST"])
@webhook
def webhook_pull_request(data):
    return ""

@app.route("/push", methods = ["POST"])
@webhook
def webhook_push(data):
    return ""

@app.route("/release", methods = ["POST"])
@webhook
def webhook_release(data):
    return ""

@app.route("/repository", methods = ["POST"])
@webhook
def webhook_repository(data):
    return ""

@app.route("/vulnerability", methods = ["POST"])
@webhook
def webhook_vulnerability(data):
    return ""

@app.route("/repo-visibility", methods = ["POST"])
@webhook
def webhook_repo_visibility(data):
    return ""
