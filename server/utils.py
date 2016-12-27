# -*- coding: utf-8 -*-
"""
    A Flask version of the PDB2PQR server
    ~~~~~~~~

    Utilities for the PDB2PQR server

    :copyright: (c) 2016 Battelle, etc.
    :license: BSD, see LICENSE for more details.
"""
import os
import os.path
import time
from flask import render_template, url_for


def local_job_dir(tmp_path, job_id):
    """ Get the path to the job dir """
    path = os.path.join(tmp_path, job_id)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def job_files(tmp_path, job_id):
    """ Get a dictionary of files in the job directory """
    path = local_job_dir(tmp_path, job_id)
    file_dict = {}
    for file_name in os.listdir(path):
        file_dict[file_name] = url_for("job_file", filename=file_name, jobid=job_id)
    return file_dict


def set_job_id(_time=None):
    """ Given a floating point time.time(), generate a job ID. Use the tenths of a second to
    differentiate.  Return job id as string """
    if not _time:
        _time = time.time()
    id_str = "%s" % _time
    period = id_str.find(".")
    _id = "%s%s" % (id_str[:period], id_str[(period + 1):(period + 2)])
    print(_id)
    return _id


def generic_error(error, code=None):
    """ A generic handler for web page errors """
    return render_template("error.html", error=error), code
