from flask import request, abort
from model import *

def user_from_token():
    """Get the user object from the token GET/POST parameter."""
    if request.method == "POST":
        tok = request.form["token"]
    else:
        tok = request.args.get("token")

    token = Token.query.filter_by(token=tok).first()
    if not token:
        abort(401)
    else:
        return token.user

def get_file():
    user = user_from_token()
    if request.method == "POST":
        r = request.form
    else:
        r = request.args

    path = r["path"]

    # who actually owns the file: us, or another user?
    try:
        target = User.query.filter_by(username=r["user"]).first()
        if target is None:
            abort(403)
    except KeyError:
        target = user

    file = EncryptedFile.query.filter_by(owner=target, owner_path=path).first()

    # if requesting someone else's file
    if user != target:
        # if it exists and we have access, return it
        if file is not None and user in file.shared_users:
            return file
        # else abort
        else:
            abort(403)
    else:
        return file

def process_metadata(enc_file, event_type):
    metadata = request.form["metadata"]
    signature = request.form["metadata_signature"]
    if request.method == "POST":
        r = request.form
    else:
        r = request.args

    originator = user_from_token()


    # create Events for each user that this file is shared with, other
    # than the person who started the event
    to_notify = enc_file.shared_users + [enc_file.owner]
    events = [Event(user, metadata, event_type, signature) for user in to_notify if user != originator]
    db.session.add_all(events)
    db.session.commit()

