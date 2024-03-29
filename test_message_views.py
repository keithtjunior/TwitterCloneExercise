"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()


    def tearDown(self):
        """Clean up transactions"""

        db.session.rollback()
        db.session.close()


    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")


    def test_messages_show(self):
        """Is message shown?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            msg = Message(text='Hello', user_id=self.testuser.id)

            db.session.add(msg)
            db.session.commit()

            resp = c.get(f'/messages/{msg.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="message-area">', html)


    def test_messages_destroy(self):
        """Can user delete a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            msg = Message(text='Hello', user_id=self.testuser.id)

            db.session.add(msg)
            db.session.commit()

            resp = c.post(f'/messages/{msg.id}/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<ul class="user-stats nav nav-pills">', html)


    def test_add_message_unauth(self):
        """Can unauth user add a message"""

        resp = self.client.post('/messages/new', data={'text': 'Hello'})

        self.assertEqual(resp.status_code, 302)

        resp = self.client.post('/messages/new', data={'text': 'Hello'}, 
                                follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)


    def test_messages_destroy_unauth(self):
        """Can unauth user delete a message"""

        msg = Message(text='Hello', user_id=self.testuser.id)

        db.session.add(msg)
        db.session.commit()

        resp = self.client.post(f'/messages/{msg.id}/delete')

        self.assertEqual(resp.status_code, 302)

        resp = self.client.post(f'/messages/{msg.id}/delete', follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<a href="/signup" class="btn btn-primary">Sign up</a>', html)
