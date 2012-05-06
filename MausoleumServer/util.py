from flask import request
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
        path = request.form["path"]
    else:
        path = request.args.get("path")

    return EncryptedFile.query.filter_by(owner_id=user.id, owner_path=path).first()

def process_metadata(enc_file, event_type):
    metadata = request.form["metadata"]
    signature = request.form["metadata_signature"]

    # create Events for each user that this file is shared with
    to_notify = enc_file.shared_users
    events = [Event(user, metadata, event_type, signature) for user in to_notify]
    db.session.add_all(events)
    db.session.commit()
