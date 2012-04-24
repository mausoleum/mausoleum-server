from model import *
from flask import g, Flask, request, abort, jsonify
import bcrypt, os

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

    print request.form["username"]
    user = User.get(request.form["username"], request.form["password"])
    if user is None:
        abort(403)

    if user.token: token = user.token
    else:
        token = Token()
        token.token = os.urandom(256).encode("base64")[:128]
        token.user = user
        db.session.add(token)
        db.session.commit()

    return jsonify(token=token.token)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')


