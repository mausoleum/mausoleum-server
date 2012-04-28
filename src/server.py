from model import *
from flask import g, Flask, request, abort, jsonify
import bcrypt, os, base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mausoleum.db'
db.app = app
db.init_app(app)
db.create_all()

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
        token.token = base64.b64encode(os.urandom(256))[:128]
        print token.token
        token.user = user
        db.session.add(token)
        db.session.commit()

    return jsonify(token=token.token)

@app.route('/file', methods=["POST"])
def upload():
    """Uploads a file and its metadata. Also requires the path to be specified."""
    user = user_from_token(request.form["token"])

    enc_file = EncryptedFile.query.filter_by(owner_id=user.id, owner_path=request.form["path"]).first()
    if enc_file is None:
        enc_file = EncryptedFile(user.id, request.form["path"])
    enc_file.set_contents(request.files["file"].read())
    db.session.add(enc_file)
    db.session.commit()

    return ""

@app.route('/file', methods=["GET"])
def get():
    user = user_from_token(request.args.get('token'))

    enc_file = EncryptedFile.query.filter_by(owner_id=user.id, owner_path=request.args.get("path")).first()
    if enc_file is None:
        abort(404)
    else:
        return enc_file.get_contents()

def user_from_token(tok):
    token = Token.query.filter_by(token=tok).first()
    if not token:
        abort(401)
    else:
        return token.user

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

