from rapido import db
from rapido import web
from rapido.web import request, render_template, url_for, redirect, abort

from models import Entry


USERNAME = 'admin'
PASSWORD = 'default'


@web.route('/')
def show_entries():
    entries = Entry.all().order('-pubdate').fetch(-1)
    return render_template('show_entries.html', entries=entries)


@web.route('/add', methods=['POST'])
def add_entry():
    if not request.session.get('logged_in'):
        abort(401)

    entry = Entry(title=request.form['title'], text=request.form['text'])
    entry.save()
    db.commit()
    request.flash('New entry was successfully posted')

    return redirect(url_for('show_entries'))


@web.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != USERNAME:
            error = 'Invalid username'
        elif request.form['password'] != PASSWORD:
            error = 'Invalid password'
        else:
            request.session['logged_in'] = True
            request.flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@web.route('/logout')
def logout():
    request.session.pop('logged_in', None)
    request.flash('You were logged out')
    return redirect(url_for('show_entries'))
