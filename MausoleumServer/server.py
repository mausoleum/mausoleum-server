from model import *
from util import *
from flask import g, Flask, request, abort, jsonify
import bcrypt, os, base64, json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mausoleum.db'
app.config["UPLOAD_DIR"] = '/tmp/mausoleum'

@app.route('/register', methods=["POST"])
def register():
    """Register a new user.

    username -- the username
    password -- the password

    Returns a 400 if that user already exists.
    """
    username = request.form["username"]
    password = request.form["password"]

    user = User.query.filter_by(username=username).first()
    if user is not None:
        abort(400)

    user = User(username, password)
    db.session.add(user)
    db.session.commit()

    return get_token()


@app.route('/get_token', methods=["POST"])
def get_token():
    """If the username and password are correct, returns a JSON object
    with json["token"] as the token itself. If not, causes a 403
    Forbidden.

    username -- the username
    password -- the password
    """
    user = User.get(request.form["username"], request.form["password"])
    if user is None:
        abort(403)

    if user.token: token = user.token
    else:
        token = Token()
        # Want tokens to be fixed length, it's okay if we lose a
        # little bit of data
        token.token = base64.b64encode(os.urandom(128))[:128]
        token.user = user
        db.session.add(token)
        db.session.commit()

    return jsonify(token=token.token)

@app.route('/file', methods=["POST"])
def upload():
    """Uploads a file/edits an existing file. Requires the path to be specified.

    path -- the file path
    metadata -- file upload metadata (hash of the file, etc.)
    metadata_signature -- a signature of the metadata
    user -- (optional) the user of the file
    """
    user = user_from_token()
    enc_file = get_file()
    if enc_file is None:
        enc_file = EncryptedFile(user.id, request.form["path"])

    enc_file.set_contents(request.files["file"].read())
    db.session.add(enc_file)
    db.session.commit()
    process_metadata(enc_file, "update")

    return ""

@app.route('/file', methods=["GET"])
def get():
    """Get a file from its path.

    path -- the file path
    user -- (optional) the user of the file
    """

    enc_file = get_file()
    if enc_file is None:
        abort(404)
    else:
        return enc_file.get_contents()

@app.route('/delete', methods=["POST"])
def delete():
    """Delete the file at the given path.

    path -- the file's path"""
    enc_file = get_file()
    if enc_file is None:
        abort(404)
    db.session.delete(enc_file)
    db.session.commit()
    process_metadata(enc_file, "delete")

    return ""

@app.route('/events', methods=["GET"])
def events():
    """List all the events that the user is interested in since the
    given timestamp.

    timestamp -- the timestamp to start looking at events from, in
    seconds since the epoch."""
    user = user_from_token()
    timestamp = datetime.datetime.fromtimestamp(float(request.args.get("timestamp")))
    events = Event.query.filter_by(user=user)
    relevant = and_(Event.timestamp >= timestamp, Event.user == user)
    events = Event.query.filter(relevant)

    # turn the events into JSON and return it
    return json.dumps(map(lambda x: x.to_jsonable(), events))

@app.route('/add_key', methods=["POST"])
def add_key():
    """Add an event for another user setting the key for a given
    path. Parameters are:

    user -- the target user
    path -- the path the key is for
    key -- a text representation of the actual key

    404s if the target user or target file does not exist.
    """

    user = user_from_token()
    target = request.form["user"]
    target = User.query.filter_by(username=target).first()
    if target is None:
        abort(404)

    path = request.form["path"]
    key = request.form["key"]

    # mark the file as shared to the target user
    enc_file = EncryptedFile.query.filter_by(owner=user, owner_path=path).first()
    if enc_file is None: abort(404)
    enc_file.shared_users.append(target)

    # turn the key into JSON
    obj = json.dumps({"path": path, "key": key})
    ev = Event(target, obj, "add_key")
    db.session.add_all([ev, enc_file])
    db.session.commit()

    return ""

def init_db():
    db.app = app
    db.init_app(app)
    db.create_all()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0')

