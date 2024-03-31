from card_app import app, db
from flask import render_template, redirect, url_for, flash, request, abort
from card_app.models import User, Deck, Flashcard
from card_app.forms import Deck, DeckForm, RegisterForm, LoginForm, FlashcardForm, EditFlashcardForm
from flask_login import login_user, logout_user, login_required, current_user
from random import choice

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data, email_address=form.email_address.data,password=form.password1.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account created successfully! You are now logged in as {user_to_create.username}", category='success')
        return redirect(url_for('user',username = user_to_create.username))
    if form.errors != {}: 
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')

    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(attempted_password=form.password.data):
            login_user(attempted_user)
            flash(f'Success! You are logged in as: {attempted_user.username}', category='success')
            return redirect(url_for('user',username = attempted_user.username))
        else:
            flash('Username and password are not match! Please try again', category='danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    decks = current_user.decks
    return render_template('user.html', user=user, decks = decks)

@app.route('/add_deck', methods=['GET', 'POST'])
@login_required
def add_deck():
    form = DeckForm()
    if form.validate_on_submit():
        deck = Deck(name=form.name.data)
        deck.user = current_user
        db.session.add(deck)
        db.session.commit()
        flash('Flashcard Deck added.', category='success')
        return redirect(url_for('user', username = current_user.username))
    return render_template('add_deck.html', form=form)

@app.route('/deck/<int:id>')
@login_required
def deck(id):
    deck = Deck.query.get_or_404(id)
    temp = deck.user_id
    print(temp)
    user = User.query.filter_by(id=temp).first()
    return render_template('deck.html', deck=deck, username = user.username)

@app.route('/deck/<int:id>/delete')
@login_required
def delete_deck(id):
    deck = Deck.query.get_or_404(id)
    db.session.delete(deck)
    db.session.commit()
    flash('Deck {0} has been deleted'.format(deck.name), category='success')
    return redirect(request.referrer)

@app.route('/deck/<int:id>/add_flashcard', methods=['GET', 'POST'])
@login_required
def add_flashcard(id):
    form = FlashcardForm()
    deck = Deck.query.get_or_404(id)
    if form.validate_on_submit():
        card = Flashcard(question=form.question.data, answer=form.answer.data)
        deck.flashcards.append(card)
        db.session.add(deck)
        db.session.commit()
        flash('Flashcard added to the Deck {0}'.format(deck.name), category='success')
        if form.next.data:
            return redirect(url_for('add_flashcard', id=deck.id))
        else:
            return redirect(url_for('deck', id=deck.id))
    return render_template('add_flashcard.html', form=form, name=deck.name)

@app.route('/deck/<int:deckId>/flashcard/<int:cardId>')
@login_required
def flashcard(deckId, cardId):
    deck = Deck.query.get_or_404(deckId)
    flashcard = deck.flashcards.filter_by(id=cardId).first()
    temp = deck.user_id
    user = User.query.filter_by(id=temp).first()
    if flashcard is None:
        abort(404)
    return render_template('flashcard.html', deck=deck, flashcard=flashcard, username = user.username)

@app.route('/deck/<int:deckId>/flashcard/<int:cardId>/edit', methods=['GET', 'POST'])
@login_required
def edit_flashcard(deckId, cardId):
    form = EditFlashcardForm()
    deck = Deck.query.get_or_404(deckId)
    flashcard = deck.flashcards.filter_by(id=cardId).first()
    if flashcard is None:
        abort(404)
    if form.validate_on_submit():
        flashcard.question = form.question.data
        flashcard.answer = form.answer.data
        db.session.add(flashcard)
        db.session.commit()
        flash('Flashcard was updated.', category='success')
        return redirect(url_for('flashcard', deckId=deckId, cardId=cardId))
    form.question.data = flashcard.question
    form.answer.data = flashcard.answer
    return render_template('edit_flashcard.html', form=form, flashcard=flashcard)

@app.route('/deck/<int:id>/learn')
@login_required
def learn(id):
    deck = Deck.query.get_or_404(id)
    mode = request.args.get('mode')
    if mode == 'normal':
        flashcards = deck.flashcards.filter_by(wrong_answered=False, right_answered=False).all()
    elif mode == 'wrong_ones':
        flashcards = deck.flashcards.filter_by(wrong_answered=True, right_answered=False).all()
    else:
        abort(404)
    if not flashcards:
        flash('No Cards to learn. Please reset the Cards or learn the Wrong ones if there are any.', category='info')
        return redirect(url_for('.deck', id=id))
    else:
        flashcard = choice(flashcards)
    return render_template('learn.html', flashcard=flashcard, deck=deck)

@app.route('/deck/<int:id>/reset-cards')
@login_required
def reset_cards(id):
    deck = Deck.query.get_or_404(id)
    for card in deck.flashcards.all():
        card.wrong_answered = False
        card.right_answered = False
    db.session.add(deck)
    db.session.commit()
    return redirect(url_for('.deck', id=id))

@app.route('/deck/<int:deckId>/delete_flashcard/<int:cardId>')
@login_required
def delete_card(deckId, cardId):
    flashcard = Flashcard.query.get_or_404(cardId)
    db.session.delete(flashcard)
    db.session.commit()
    return redirect(url_for('deck', id=deckId))

@app.route('/deck/<int:deckId>/learn/<int:cardId>/wrong')
@login_required
def wrong_answer(deckId, cardId):
    flashcard = Flashcard.query.get_or_404(cardId)
    flashcard.wrong_answered = True
    flashcard.right_answered = False
    db.session.add(flashcard)
    db.session.commit()
    return redirect(url_for('.learn', id=deckId, mode=request.args.get('mode')))

@app.route('/deck/<int:deckId>/learn/<int:cardId>/right')
@login_required
def right_answer(deckId, cardId):
    flashcard = Flashcard.query.get_or_404(cardId)
    flashcard.wrong_answered = False
    flashcard.right_answered = True
    db.session.add(flashcard)
    db.session.commit()
    return redirect(url_for('.learn', id=deckId, mode=request.args.get('mode')))