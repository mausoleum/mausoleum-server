import bcrypt, hashlib, os, datetime, json, time
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import and_

db = SQLAlchemy()

shared_files = db.Table('sharing',
                     db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('file_id', db.Integer, db.ForeignKey('encrypted_file.id'))
)

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    token = db.relationship('Token', backref='user', uselist=False)
    files = db.relationship('EncryptedFile', backref='owner')
    shared_files = db.relationship('EncryptedFile', backref='shared_users', secondary=shared_files)
    events = db.relationship('Event', backref='user')

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


class EncryptedFile(db.Model):
    __tablename__ = "encrypted_file"

    id = db.Column(db.Integer, primary_key=True)
    disk_path = db.Column(db.Text, unique=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner_path = db.Column(db.Text)

    def __init__(self, owner_id, owner_path):
        self.owner_id = owner_id
        self.owner_path = owner_path

    def get_contents(self):
        f = open(self.disk_path, 'r')
        return f.read()

    def set_contents(self, contents):
        """Set the contents of the file. Note that this causes a new
        file to be created, and the old one is not deleted."""
        digest = hashlib.sha256(contents).hexdigest()
        dir_name = os.path.join(db.app.config["UPLOAD_DIR"], digest[0:2])
        # make the digest directory shard if it doesn't exist
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        path = os.path.join(dir_name, digest)

        # write the data out
        with open(path, "w") as f:
            f.write(contents)

        self.disk_path = path
        return path



class Event(db.Model):
    """Models an event that a user needs to be notified of."""
    __tablename__ = "event"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime(False))
    signature = db.Column(db.Text)
    contents = db.Column(db.Text)
    type = db.Column(db.Text)

    def __init__(self, user, contents, event_type, signature=None):
        self.user = user
        self.contents = contents
        self.signature = signature
        self.type = event_type
        self.timestamp = datetime.datetime.utcnow()

    def to_jsonable(self):
        """Serializes an Event object into its timestamp and
        contents. The timestamp is in seconds since the Unix epoch."""
        d = {"timestamp": time.mktime(self.timestamp.timetuple()), "contents": self.contents, "type": self.type}
        if self.signature: d["signature"] = self.signature
        return {"timestamp": time.mktime(self.timestamp.timetuple()), "contents": self.contents, "signature": self.signature, "type": self.type}
