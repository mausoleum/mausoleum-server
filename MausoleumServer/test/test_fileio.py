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
        user = User(**self.default_user)
        server.db.session.add(user)
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
               'file': (StringIO('This is a test'), 'blah.txt'),
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
               'user': 'username', 'key': 'a key'}
        result = self.app.post('/add_key', data=req)
        self.assertEquals(result.status_code, 200)

    def test_set_key(self):
        self.test_add_key()
        req = {'token': self.token, 'path': 'test.txt',
               'user': 'username'}
        result = self.app.get('/file/key', query_string=req)
        self.assertEquals(result.data, "a key")

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

if __name__ == '__main__':
    unittest.main()
