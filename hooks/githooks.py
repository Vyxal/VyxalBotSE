from main import app
from utils import *

@app.route("/branch-tag-created", methods = ["POST"])
@webhook
def webhook_branch_tag_created():
    return ""

@app.route("/branch-tag-deleted", methods = ["POST"])
@webhook
def webhook_branch_tag_deleted():
    return ""

@app.route("/discussion", methods = ["POST"])
@webhook
def webhook_discussion():
    return ""

@app.route("/fork", methods = ["POST"])
@webhook
def webhook_fork():
    return ""

@app.route("/issue", methods = ["POST"])
@webhook
def webhook_issue():
    return ""

@app.route("/organization", methods = ["POST"])
@webhook
def webhook_organization():
    return ""

@app.route("/pr-review-comment", methods = ["POST"])
@webhook
def webhook_pr_review_comment():
    return ""

@app.route("/pr-review-thread", methods = ["POST"])
@webhook
def webhook_pr_review_thread():
    return ""

@app.route("/pr-review", methods = ["POST"])
@webhook
def webhook_pr_review():
    return ""

@app.route("/pull-request", methods = ["POST"])
@webhook
def webhook_pull_request():
    return ""

@app.route("/push", methods = ["POST"])
@webhook
def webhook_push():
    return ""

@app.route("/release", methods = ["POST"])
@webhook
def webhook_release():
    return ""

@app.route("/repository", methods = ["POST"])
@webhook
def webhook_repository():
    return ""

@app.route("/vulnerability", methods = ["POST"])
@webhook
def webhook_vulnerability():
    return ""

@app.route("/repo-visibility", methods = ["POST"])
@webhook
def webhook_repo_visibility():
    return ""
