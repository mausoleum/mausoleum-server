import unittest
import tempfile
import requests
import os
import json
import base64
from StringIO import StringIO

from MausoleumServer import server
from MausoleumServer.model import *

class TestFileIO(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        server.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
            self.db_path
        server.app.config['TESTING'] = True
        self.app = server.app.test_client()
        server.init_db()

        self.default_user = {'username': 'username', 'password': 'password'}
        self.other_user = {'username': 'username2', 'password': 'password2'}
        user = User(**self.default_user)
        user2 = User(**self.other_user)
        server.db.session.add_all([user, user2])
        server.db.session.commit()

    def test_get_token(self):
        result = self.app.post('/get_token', data=self.default_user)
        self.assertEquals(result.status_code, 200)

        self.token = json.loads(result.data)['token']
        self.assertEquals(len(self.token), 128)

    def test_get_token_invalid_creds(self):
        baduser = {'username': 'asdf', 'password': 'doesntexist'}
        result = self.app.post('/get_token', data=baduser)

        self.assertEquals(result.status_code, 403)

    def test_upload_file(self):
        self.test_get_token()
        req = {'token': self.token, 'path': 'test.txt',
               'file': (StringIO('File contents'), 'blah.txt'),
               'metadata': 'foo', 'metadata_signature': 'bar'}
        result = self.app.post('/file', data=req)
        self.assertEquals(result.status_code, 200)

    def test_download_file(self):
        self.test_upload_file()
        req = {'token': self.token, 'path': 'test.txt'}
        result = self.app.get('/file', query_string=req)
        self.assertEquals(result.status_code, 200)

    def test_add_key(self):
        self.test_upload_file()
        req = {'token': self.token, 'path': 'test.txt',
               'user': 'username2', 'key': 'a key',
               'metadata_signature': 'meta_sig'}
        result = self.app.post('/file/key', data=req)

        tok = self.app.post('/get_token', data=self.other_user).data
        self.other_token = json.loads(tok)["token"]

        self.assertEquals(result.status_code, 200)

    def test_get_key(self):
        self.test_add_key()
        req = {'token': self.other_token, 'path': 'test.txt',
               'user': 'username'}
        result = self.app.get('/file/key', query_string=req)
        self.assertEquals(result.data, "a key")

    def test_share_file(self):
        self.test_add_key()

        contents = self.app.get('/file', query_string={"token": self.other_token,
                                                        "path": "test.txt",
                                                        "user": "username"}).data

        self.assertEquals(contents, "File contents")

    def test_metadata(self):
        self.test_add_key()

        result = self.app.get('/file/metadata', query_string={"token": self.other_token,
                                                              "user": "username",
                                                              "path": "test.txt",
                                                              }).data
        goal = {u"contents": u'{"path": "test.txt", "key": "a key"}',
                u"signature": u"meta_sig",
                u"type": u"add_key"}
        parsed = json.loads(result)

        # don't test timestamp so we don't have to deal with timing issues
        del parsed["timestamp"]
        self.assertEquals(parsed, goal)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

if __name__ == '__main__':
    unittest.main()
