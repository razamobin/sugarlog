import os
import sugarlog
import unittest
from sugarlog import redis

class SugarlogTestCase(unittest.TestCase):
    def setUp(self):
        sugarlog.app.config['REDIS_HOST'] = '127.0.0.1'
        sugarlog.app.config['REDIS_PORT'] = '7379'
        sugarlog.app.config['TESTING'] = True
        self.app = sugarlog.app.test_client()

    def tearDown(self):
        redis_db = redis.Redis(host=sugarlog.app.config['REDIS_HOST'], port=int(sugarlog.app.config['REDIS_PORT']))
        redis_db.flushall()
        redis_db.connection.disconnect()

    def test_empty_db(self):
        rv = self.app.get('/')
        assert 'sugar log' in rv.data
        assert 'sign up' in rv.data
        assert 'log in' in rv.data

    def new_entry(self):
        return self.app.post('/new', data=dict(
            day='2010-12-13',
            time='9.30pm',
            blood_sugar='96',
            notes='great day today, ate eggs, cream, fish, butter, vegetables, beef'
        ), follow_redirects=True)

    def test_first_entry(self):
        rv = self.app.get('/')
        assert 'great day today, ate eggs, cream, fish, butter, vegetables, beef' not in rv.data
        self.new_entry()
        rv = self.app.get('/')
        assert 'great day today, ate eggs, cream, fish, butter, vegetables, beef' in rv.data

    def test_signup_login(self):
        rv = self.app.post('/login', data=dict(
            first_name='Raza',
            password='123456'
        ), follow_redirects=True)
        assert 'action="/login"' in rv.data

        rv = self.app.post('/signup', data=dict(
            first_name='Raza',
            password='123456'
        ), follow_redirects=True)
        assert 'action="/login"' not in rv.data
        assert 'action="/signup"' not in rv.data

        rv = self.app.get('/')
        assert 'hello' in rv.data
        assert 'Raza' in rv.data

        rv = self.app.get('/logout')

        rv = self.app.get('/')
        assert 'hello' not in rv.data
        assert 'Raza' not in rv.data

        rv = self.app.post('/login', data=dict(
            first_name='Raza',
            password='123456'
        ), follow_redirects=True)
        assert 'action="/login"' not in rv.data

    def test_reply(self):
        self.new_entry()
        rv = self.app.get('/')
        assert 'nice job' not in rv.data
        rv = self.app.post('/comments', data=dict(
            entry_id='1',
            author='Raza',
            comment='nice job'
        ), follow_redirects=True)

        rv = self.app.get('/')
        assert 'nice job' in rv.data

    def test_signup_on_post(self):
        rv = self.app.get('/')
        assert 'hello' not in rv.data
        assert 'Pervez' not in rv.data
        assert 'log in' in rv.data
        self.new_entry()

        rv = self.app.get('/')
        assert 'hello' in rv.data
        assert 'Pervez' in rv.data
        assert 'logout' in rv.data

        rv = self.app.get('/logout', follow_redirects=True)
        assert 'hello' not in rv.data
        assert 'Pervez' not in rv.data
        assert 'log in' in rv.data

        self.new_entry()
        rv = self.app.get('/')
        assert 'hello' in rv.data
        assert 'Pervez' in rv.data
        assert 'logout' in rv.data

if __name__ == '__main__':
    unittest.main()
