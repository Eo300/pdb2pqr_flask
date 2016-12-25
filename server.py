# -*- coding: utf-8 -*-
"""
    A Flask version of the PDB2PQR server
    ~~~~~~~~

    This was modeled after the minitwit example in the Flask distribution

    :copyright: (c) 2016 Battelle, etc.
    :license: BSD, see LICENSE for more details.
"""

import time
import os, os.path
import json
from sqlite3 import dbapi2 as sqlite3
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack, \
     send_from_directory
from werkzeug.utils import secure_filename

# Configuration
""" Database file """
DATABASE_DIR = os.path.normpath("./data")
DATABASE = os.path.join(DATABASE_DIR, "pdb2pqr_server.db")
""" Upload directory """
UPLOADS_DIR = os.path.normpath("./uploads")
""" Debug status """
DEBUG = True
""" PDB2PQR version number (should be replaced automatically) """
# TODO - replace this with auto-configured version number
PDB2PQR_VERSION = "13.666"

# Create the application
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('PDB2PQR_SETTINGS', silent=True)

# TODO - move some of this to a utils module

def store_files(file_dict, job_id):
    """ Store uploaded files """
    upload_dir = app.config["UPLOADS_DIR"]
    storage_dict = {}
    for key, file_obj in file_dict.items():
        file_name = secure_filename(file_obj.filename)
        if file_name:
            file_name = "%s-%s" % (job_id, file_name)
            file_path = os.path.join(upload_dir, file_name)
            print(file_path)
            file_obj.save(file_path)
            storage_dict[key] = url_for("uploaded_file", filename=file_name)
    return storage_dict

@app.route('/%s/<filename>' % UPLOADS_DIR)
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOADS_DIR'], filename)

def set_job_id(_time=None):
    """
        Given a floating point time.time(), generate a job ID.
        Use the tenths of a second to differentiate.
        Parameters
            time:  The current time.time() (float)
        Returns
            id  :  The file id (string)
    """
    if not _time:
        _time = time.time()
    strID = "%s" % _time
    period = strID.find(".")
    _id = "%s%s" % (strID[:period], strID[(period+1):(period+2)])
    print(_time, _id)
    return _id


def get_db():
    """ Opens a new database connection if there is none yet for the
    current application context. """
    database_path = app.config["DATABASE"]
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(database_path)
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
    """ Closes the database again at the end of the request. """
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def setup():
    """ Initializes the database, creates directories, etc. """
    for path in [app.config["DATABASE_DIR"], app.config["UPLOADS_DIR"]]:
        print("Checking %s..." % path)
        if not os.path.exists(path):
            print("Creating %s..." % path)
            os.makedirs(path)
    print("Initializing database...")
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('setup')
def setup_command():
    """ Creates the database tables, directories, etc. """
    setup()


def query_db(query, args=(), one=False):
    """ Queries the database and returns a list of dictionaries. """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


@app.before_request
def before_request():
    g.job_id = None
    if 'job_id' in session:
        # TODO - this should display the starting screen and/or database
        return "Got a before_request() call..."


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
        g.job_id = set_job_id()
        file_dict = store_files(request.files, g.job_id)
        print(request.files)
        print(request.form)
        return render_template("start_job.html", job_id=g.job_id, form=request.form, files=file_dict)
    else:
        return render_template("config_job.html")


# add some filters to jinja
# app.jinja_env.filters['datetimeformat'] = format_datetime