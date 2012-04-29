from model import *
from flask import g, Flask, request, abort, jsonify
import bcrypt, os, base64, json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mausoleum.db'
app.config["UPLOAD_DIR"] = '/tmp/mausoleum'

@app.route('/get_token', methods=["POST"])
def get_token():
    """If the username and password are correct, sets a cookie labeled
    'token' with an authentication token good for the next 24
    hours. If not, causes a 403 Forbidden."""
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
    """Uploads a file/edits an existing file. Requires the path to be specified."""
    user = user_from_token()
    enc_file = get_file()
    if enc_file is None:
        enc_file = EncryptedFile(user.id, request.form["path"])
    enc_file.set_contents(request.files["file"].read())
    db.session.add(enc_file)
    db.session.commit()

    return ""

@app.route('/file', methods=["GET"])
def get():
    """Get a file from its path."""
    enc_file = get_file()
    if enc_file is None:
        abort(404)
    else:
        return enc_file.get_contents()

@app.route('/delete', methods=["POST"])
def delete():
    """Delete the file at the given path."""
    enc_file = get_file()
    if enc_file is None:
        abort(404)
    db.session.delete(enc_file)
    db.session.commit()

    return ""

@app.route('/events', methods=["GET"])
def events():
    user = user_from_token()
    timestamp = datetime.datetime.fromtimestamp(float(request.args.get("timestamp")))
    events = Event.query.filter_by(user=user)
    relevant = and_(Event.timestamp >= timestamp, Event.user == user)
    events = Event.query.filter(relevant)

    # turn the events into JSON and return it
    return json.dumps(map(lambda x: x.to_jsonable(), events))

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

def init_db():
    db.app = app
    db.init_app(app)
    db.create_all()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host='0.0.0.0')

