"""User View tests"""

import os
import bcrypt
from unittest import TestCase

from models import db, connect_db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

connect_db(app)


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="HASHED_PASSWORD",
                                    image_url=None)
        self.testuser2 = User(username="testuser2",
                            email="test2@test.com",
                            password="HASHED_PASSWORD",
                            image_url=None)
        
        db.session.add(self.testuser2)
        db.session.commit()

        self.user_id_1 = self.testuser.id
        self.user_id_2 = self.testuser2.id

        f = Follows(
                user_being_followed_id=self.user_id_2,
                user_following_id=self.user_id_1
            )

        db.session.add(f)
        db.session.commit()


    def tearDown(self):
        """Clean up transactions"""

        db.session.rollback()
        db.session.close()


    def test_signup(self):
        """Can you register a new user?"""

        new_user = {'username': 'newuser',
                    'email': 'new@new.com',
                    'password': 'HASHED_PASSWORD',
                    'image_url': None}

        resp = self.client.post('/signup', data=new_user)

        self.assertEqual(resp.status_code, 302)

        u = User.query.filter_by(username='newuser').first()
        self.assertEqual(User, type(u))
        self.assertEqual(u.email, 'new@new.com')


    def test_login(self):
        """Can user login?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id_1

            resp = c.get('/', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<ul class="user-stats nav nav-pills">', html)


    def test_list_users(self):
        """Can logged in user view listing of users?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id_1

            resp = c.get('/users')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<input name="q" class="form-control" placeholder="Search Warbler" id="search">', html)


    def test_users_show(self):
        """Can logged in user view another user's profile?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id_1

            resp = c.get(f'/users/{self.user_id_2}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<a href="/users/{self.user_id_2}/followers">', html)
        

    def test_show_following(self):
        """Can logged in user view following list?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id_1

            resp = c.get(f'/users/{self.user_id_1}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-lg-4 col-md-6 col-12">', html)


    def test_users_followers(self):
        """Can logged in user view followers list?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id_1

            f = Follows(
                user_being_followed_id=self.user_id_1,
                user_following_id=self.user_id_2
            )

            db.session.add(f)
            db.session.commit()

            resp = c.get(f'/users/{self.user_id_1}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p class="card-bio">', html)


    def test_add_follow(self):
        """Can logged in user add a follow?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id_1

            resp = c.post(f'/users/follow/{self.user_id_2}', 
                                    follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-lg-4 col-md-6 col-12">', html)


    def test_stop_following(self):
        """Can logged in user remove a follow?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user_id_1

            resp = c.post(f'/users/stop-following/{self.user_id_2}', 
                                    follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="col-sm-9">', html)

            
    def test_show_following_unath(self):
        """Can unauth user view following list?"""

        resp = self.client.get(f'/users/{self.user_id_1}/following')

        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(f'/users/{self.user_id_1}/following', 
                               follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)


    def test_users_followers_unath(self):
        """Can unauth user view followers list?"""

        resp = self.client.get(f'/users/{self.user_id_1}/followers')

        self.assertEqual(resp.status_code, 302)

        resp = self.client.get(f'/users/{self.user_id_1}/followers', 
                               follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)


    def test_add_follow_unath(self):
        """Can unauth user add a follow?"""

        resp = self.client.post(f'/users/follow/{self.user_id_2}')

        self.assertEqual(resp.status_code, 302)

        resp = self.client.post(f'/users/follow/{self.user_id_2}', 
                                follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)


    def test_stop_following_unath(self):
        """Can unauth user remove a follow?"""

        resp = self.client.post(f'/users/stop-following/{self.user_id_2}')

        self.assertEqual(resp.status_code, 302)

        resp = self.client.post(f'/users/stop-following/{self.user_id_2}', 
                                follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)