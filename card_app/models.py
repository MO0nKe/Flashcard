from card_app import db, login_manager
from card_app import bcrypt
from flask_login import UserMixin
from datetime import datetime
import bleach
from markdown import markdown

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    decks = db.relationship('Deck', backref = 'user', lazy=True)

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

class Deck(db.Model):
    __tablename__ = 'deck'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    flashcards = db.relationship('Flashcard', backref='deck', cascade = "all,delete-orphan", lazy='dynamic')

    def __repr__(self):
        return '<Flashcard Deck: %r>' % self.name

class Flashcard(db.Model):
    __tablename__ = 'flashcard'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(),nullable=False)
    question_html = db.Column(db.Text)
    answer = db.Column(db.String(),nullable=False)
    answer_html = db.Column(db.Text)
    deck_id = db.Column(db.Integer, db.ForeignKey('deck.id'), nullable = False)
    right_answered = db.Column(db.Boolean, default=False)
    wrong_answered = db.Column(db.Boolean, default=False)

    @staticmethod
    def on_changed_question(target, value, oldvalue, initiator):
        allowed_tags = ['abbr', 'acronym', 'b', 'blockquote', 'code', 'i',
                        'li', 'ol', 'strong', 'ul', 'h1', 'h2', 'h3', 'p']
        target.question_html = bleach.clean(markdown(value, output_format='html'), tags=allowed_tags, strip=True)

    @staticmethod
    def on_changed_answer(target, value, oldvalue, initiator):
        allowed_tags = ['abbr', 'acronym', 'b', 'blockquote', 'code', 'i',
                        'li', 'ol', 'strong', 'ul', 'h1', 'h2', 'h3', 'p']
        target.answer_html = bleach.clean(markdown(value, output_format='html'), tags=allowed_tags, strip=True)

    def __repr__(self):
        return '<Flashcard: %r>' % self.id

db.event.listen(Flashcard.answer, 'set', Flashcard.on_changed_answer)
db.event.listen(Flashcard.question, 'set', Flashcard.on_changed_question)
