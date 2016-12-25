# -*- coding: utf-8 -*-
"""
    A Flask version of the PDB2PQR server
    ~~~~~~~~

    This was modeled after the minitwit example in the Flask distribution

    :copyright: (c) 2016 Battelle, etc.
    :license: BSD, see LICENSE for more details.
"""

import time
from sqlite3 import dbapi2 as sqlite3
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack

# Configuration
DATABASE = '/tmp/pdb2pqr_server.db'
DEBUG = True
PDB2PQR_VERSION = "13.666"

# Create the application
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('PDB2PQR_SETTINGS', silent=True)


def get_db():
    """ Opens a new database connection if there is none yet for the
    current application context. """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
    """ Closes the database again at the end of the request. """
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def init_db():
    """ Initializes the database. """
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """ Creates the database tables. """
    init_db()
    print('Initialized the database.')


def query_db(query, args=(), one=False):
    """ Queries the database and returns a list of dictionaries. """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


@app.before_request
def before_request():
    g.job_id = None
    if 'user_id' in session:
        # TODO - this should display the starting screen and/or database
        pass


@app.route('/', methods=["GET", "POST"])
def server_main():
    """ Show the main PDB2PQR server page """
    # TODO - I'm debugging here
    print(request.remote_addr)
    # TODO - this configuration should happen somewhere else
    g.pdb2pqr_version = PDB2PQR_VERSION
    if g.job_id:
        return redirect(url_for('job_status'))
    elif request.method == "POST":
        # TODO - launch job
        print(request)
        pass
    else:
        return render_template("config_job.html")

@app.route('/job_status')
def job_status():
    """Displays the latest messages of all users."""
    return render_template('job_status.html', job_id=g.job_id)


@app.route('/database')
def dump_data(username):
    """Display's a users tweets."""
    # TODO - show data from database
    abort(404)


@app.route('/add_message', methods=['POST'])
def add_message():
    """Registers a new message for the user."""
    if 'user_id' not in session:
        abort(401)
    if request.form['text']:
        db = get_db()
        db.execute('''insert into message (author_id, text, pub_date)
          values (?, ?, ?)''', (session['user_id'], request.form['text'],
                                int(time.time())))
        db.commit()
        flash('Your message was recorded')
    return redirect(url_for('timeline'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        user = query_db('''select * from user where
            username = ?''', [request.form['username']], one=True)
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['pw_hash'],
                                     request.form['password']):
            error = 'Invalid password'
        else:
            flash('You were logged in')
            session['user_id'] = user['user_id']
            return redirect(url_for('timeline'))
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_user_id(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            db = get_db()
            db.execute('''insert into user (
              username, email, pw_hash) values (?, ?, ?)''',
              [request.form['username'], request.form['email'],
               generate_password_hash(request.form['password'])])
            db.commit()
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)

# add some filters to jinja
# app.jinja_env.filters['datetimeformat'] = format_datetime