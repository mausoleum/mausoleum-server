import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    password_hash = db.Column(db.String(), nullable=False)
    token = db.relationship('Token', backref='user', uselist=False)

    def __init__(self, username, password):
        self.username = username
        self.password_hash = bcrypt.hashpw(password, bcrypt.gensalt())

    @classmethod
    def get(cls, username, password):
        """Get the user with the given username and password. Returns
        None if there is no such user (invalid username or
        password)."""
        user = cls.query.filter_by(username=username).first()

        if user is None: return None
        elif bcrypt.hashpw(password, user.password_hash) == user.password_hash:
            return user
        else:
            return None

    def __repr__(self):
        return "<User %r>" % self.username


class Token(db.Model):
    __tablename__ = "token"

    token = db.Column(db.String(128), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.username'))

    def __repr__(self):
        return "<Token %r>" % self.token
