# -*- coding: utf-8 -*-
"""
    A Flask version of the PDB2PQR server
    ~~~~~~~~

    This was modeled after the minitwit example in the Flask distribution

    :copyright: (c) 2016 Battelle, etc.
    :license: BSD, see LICENSE for more details.
"""

import os
import os.path
from flask import Flask, request, url_for, redirect, render_template, \
     g, send_from_directory
from . import utils
from . import config


# Create the application
APP = Flask(__name__)
APP.config.from_object(config)
APP.config.from_envvar('PDB2PQR_SETTINGS', silent=True)


def setup():
    """ Initializes the database, creates directories, etc. """
    for path in [APP.config["JOBS_DIR"]]:
        print("Checking %s..." % path)
        if not os.path.exists(path):
            print("Creating %s..." % path)
            os.makedirs(path)


@APP.before_request
def before_request():
    """ Set up globals before request processed """
    g.job_id = None


@APP.cli.command('setup')
def setup_command():
    """ Creates the database tables, directories, etc. """
    setup()


@APP.route('/%s/<filename>' % APP.config["JOBS_DIR"])
def job_file(filename):
    """ Deliver a job file """
    return send_from_directory(APP.config['JOBS_DIR'], filename)


@APP.route('/', methods=["GET", "POST"])
def server_main():
    """ Show the main PDB2PQR server page """
    # TODO - I'm debugging here
    print(request.remote_addr)
    # TODO - this configuration should happen somewhere else
    g.pdb2pqr_version = APP.config["PDB2PQR_VERSION"]
    if g.job_id:
        return redirect(url_for('job_status'))
    elif request.method == "POST":
        # TODO - launch job
        g.job_id = utils.set_job_id()
        file_dict = utils.store_files(file_dict=request.files, job_id=g.job_id,
                                      job_dir=APP.config["JOBS_DIR"])
        utils.save_options(form_dict=request.form, job_id=g.job_id,
                           file_dict=file_dict, job_dir=APP.config["JOBS_DIR"])
        return render_template("start_job.html", job_id=g.job_id,
                               form=request.form, files=file_dict)
    else:
        return render_template("config_job.html")
