"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
import bcrypt
from unittest import TestCase

from models import db, User, Message, Follows
from app import app
from sqlalchemy import exc


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()


    def tearDown(self):
        """Clean up transactions"""

        db.session.rollback()
        db.session.close()


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    def test__repr__(self):
        """Does the repr dunder method work as expected?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        r = repr(u)

        self.assertEqual(r, f'<User #{u.id}: testuser, test@test.com>')


    def test_is_followed_by(self):
        """
        Does is_followed_by successfully detect when user1 is not followed by user2?
        Does is_followed_by successfully detect when user1 is followed by user2?
        """
        
        user1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"     
        )

        db.session.add_all([user1, user2])
        db.session.commit()
        
        self.assertEqual(user1.is_followed_by(user2), False)
        
        f = Follows(
            user_being_followed_id=user1.id,
            user_following_id=user2.id
        )

        db.session.add(f)
        db.session.commit()

        self.assertEqual(user1.is_followed_by(user2), True)


    def test_is_following(self):
        """
        Does is_following successfully detect when user1 is not following user2?
        Does is_following successfully detect when user1 is following user2?
        """

        user1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        user2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"     
        )

        db.session.add_all([user1, user2])
        db.session.commit()
        
        self.assertEqual(user1.is_following(user2), False)
        
        f = Follows(
            user_being_followed_id=user2.id,
            user_following_id=user1.id
        )

        db.session.add(f)
        db.session.commit()

        self.assertEqual(user1.is_following(user2), True)


    def test_signup(self):
        """
        Does signup successfully create a new user given valid credentials?
        Does signup fail to create a new user if any of the validations fail?
        """
        
        username="testuser"
        email="test@test.com"
        password="HASHED_PASSWORD"
        image_url=""

        user = User.signup(username, email, password, image_url)
        db.session.commit()

        self.assertEqual(str(user), repr(user))

        username2="testuser"
        email2="test2@test.com"
        password2="HASHED_PASSWORD"
        image_url2=""

        # raise IntegrityError when key value (username) already exists"   
        with self.assertRaises(exc.IntegrityError) as context:
            User.signup(username2, email2, password2, image_url2)
            db.session.commit()

        self.assertEqual(type(context.exception), exc.IntegrityError)

        self.tearDown()

        username3="testuser3"
        email3=None
        password3="HASHED_PASSWORD"
        image_url3=""

        # raise IntegrityError when key value (email) is missing"   
        with self.assertRaises(exc.IntegrityError) as context:
            User.signup(username3, email3, password3, image_url3)
            db.session.commit()

        self.assertEqual(type(context.exception), exc.IntegrityError)
        

    def test_authenticate(self):
        """
        Does authenticate successfully return a user w/ a valid username and password?
        Does authenticate successfully fail to return a user when the username is invalid?
        Does authenticate successfully fail to return a user when the password is invalid?
        """

        # convert password hash into UTF8 then decode to prevent duplicate encoding
        pwd = "HASHED_PASSWORD"
        password_hash = bcrypt.hashpw(pwd.encode('utf8'), bcrypt.gensalt())
        password_decode = password_hash.decode('utf8')

        u = User(
                username="testuser",
                email="test@test.com",
                password=password_decode
            )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(User.authenticate(u.username, pwd), u)
        self.assertEqual(User.authenticate('testuser2', pwd), False)
        self.assertEqual(User.authenticate(u.username, 'HASHEDPASSWORD'), False)