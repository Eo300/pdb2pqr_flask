# -*- coding: utf-8 -*-
"""
    A Flask version of the PDB2PQR server
    ~~~~~~~~

    This was modeled after the minitwit example in the Flask distribution

    :copyright: (c) 2016 Battelle, etc.
    :license: BSD, see LICENSE for more details.
"""

from flask import Flask, request, render_template, g, send_from_directory
from . import utils
from . import job


# Create the application
app = Flask(__name__)
app.config["DEBUG"] = True
_TMP_PATH = app.instance_path
# TODO - Assign version number automatically
_PDB2PQR_VERSION = "13.666"


@app.before_request
def before_request():
    """ Set up globals before request processed """
    g.job = None

@app.route("/job/<jobid>")
def job_status(jobid):
    """ Update job status """
    # TODO - dynamically check for job status
    job_status = job.STATUS_DIED
    job_files = utils.job_files(tmp_path=_TMP_PATH, job_id=jobid)
    return render_template("job_status.html", job_id=jobid, job_files=job_files,
                           job_status=job_status)

@app.route('/job/<jobid>/<filename>')
def job_file(filename, jobid):
    """ Deliver a job file """
    path = utils.local_job_dir(tmp_path=_TMP_PATH, job_id=jobid)
    return send_from_directory(path, filename)


@app.route('/', methods=["GET", "POST"])
def server_main():
    """ Show the main PDB2PQR server page """
    # TODO - I'm debugging here
    print(request.remote_addr)
    # TODO - this configuration should happen somewhere else
    if request.method == "POST":
        # TODO - launch job
        wopts = job.Job(req_files=request.files, req_form=request.form, tmp_path=_TMP_PATH)
        wopts.save_json()
        job_files = utils.job_files(tmp_path=_TMP_PATH, job_id=wopts.job_id)
        return render_template("start_job.html", job_id=wopts.job_id, job_files=job_files)
    else:
        return render_template("config_job.html")


@app.errorhandler(403)
def forbidden_handler(error):
    """ 403 error handler """
    return utils.generic_error(error, code=403)


@app.errorhandler(404)
def file_not_found_handler(error):
    """ 404 error handler """
    return utils.generic_error(error, code=404)


@app.errorhandler(410)
def gone_handler(error):
    """ 410 error handler """
    return utils.generic_error(error, code=410)


@app.errorhandler(500)
def internal_handler(error):
    """ 500 error handler """
    return utils.generic_error(error, code=500)


@app.errorhandler(job.JobError)
def webopt_handler(error):
    """ Something went wrong parsing web options """
    return utils.generic_error(error, code=500)
