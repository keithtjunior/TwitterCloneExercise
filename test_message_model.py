"""Message model tests."""

import os
import bcrypt
from unittest import TestCase

from models import db, User, Message, Likes
from app import app
from sqlalchemy import exc

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()


class MessageModelTestCase(TestCase):
    """Test methods for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(user)
        db.session.commit()
        self.user_id = user.id


    def tearDown(self):
        """Clean up transactions"""

        db.session.rollback()


    def test_message_model(self):
        """Does basic model work?"""

        m = Message(
            text="Hello",
            user_id=self.user_id
        )

        db.session.add(m)
        db.session.commit()

        msg = db.session.query(Message).get(m.id)

        self.assertEqual(msg.id, m.id)
        self.assertEqual(msg.text, "Hello")
        self.assertEqual(Message, type(msg))


    def test_message_user(self):
        """Does message belong to correct user"""

        m = Message(
            text="Hello",
            user_id=self.user_id
        )

        db.session.add(m)
        db.session.commit()

        msg = db.session.query(Message).get(m.id)

        self.assertEqual(self.user_id, msg.user_id)


    def test_message_likes(self):
        """Does message display correct likes"""

        m = Message(
            text="Hello",
            user_id=self.user_id
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(m.likes), 0)

        like = Likes(user_id=self.user_id, message_id=m.id)

        db.session.add(like)
        db.session.commit()

        self.assertEqual(len(m.likes), 1)
