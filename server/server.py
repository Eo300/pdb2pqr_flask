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
app = Flask(__name__)
app.config.from_object(config)
app.config.from_envvar('PDB2PQR_SETTINGS', silent=True)


def setup():
    """ Initializes the database, creates directories, etc. """
    for path in [app.config["JOBS_DIR"]]:
        print("Checking %s..." % path)
        if not os.path.exists(path):
            print("Creating %s..." % path)
            os.makedirs(path)


@app.before_request
def before_request():
    """ Set up globals before request processed """
    g.job_id = None


@app.cli.command('setup')
def setup_command():
    """ Creates the database tables, directories, etc. """
    setup()


@app.route('/%s/<filename>' % app.config["JOBS_DIR"])
def job_file(filename):
    """ Deliver a job file """
    return send_from_directory(app.config['JOBS_DIR'], filename)


@app.route('/', methods=["GET", "POST"])
def server_main():
    """ Show the main PDB2PQR server page """
    # TODO - I'm debugging here
    print(request.remote_addr)
    # TODO - this configuration should happen somewhere else
    g.pdb2pqr_version = app.config["PDB2PQR_VERSION"]
    if g.job_id:
        return redirect(url_for('job_status'))
    elif request.method == "POST":
        # TODO - launch job
        g.job_id = utils.set_job_id()
        file_dict = utils.store_files(file_dict=request.files, job_id=g.job_id,
                                      job_dir=app.config["JOBS_DIR"])
        web_options = utils.WebOptions(file_dict=file_dict,
                                       form_dict=request.form)
        web_options.save_options(job_id=g.job_id,
                                 job_dir=app.config["JOBS_DIR"])
        return render_template("start_job.html", job_id=g.job_id,
                               form=request.form, files=file_dict)
    else:
        return render_template("config_job.html")


@app.errorhandler(403)
def forbidden_handler(e):
    """ 403 error handler """
    return utils.generic_error(e, code=403)


@app.errorhandler(404)
def file_not_found_handler(e):
    """ 404 error handler """
    return utils.generic_error(e, code=404)


@app.errorhandler(410)
def gone_handler(e):
    """ 410 error handler """
    return utils.generic_error(e, code=410)


@app.errorhandler(500)
def internal_handler(e):
    """ 500 error handler """
    return utils.generic_error(e, code=500)


@app.errorhandler(utils.WebOptionsError)
def webopt_handler(e):
    """ Something went wrong parsing web options """
    return utils.generic_error(e, code=500)