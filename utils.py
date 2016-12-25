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
import json
import time
from werkzeug.utils import secure_filename
from flask import url_for

def store_files(file_dict, job_id, job_dir):
    """ Store uploaded files """
    storage_dict = {}
    for key, file_obj in file_dict.items():
        file_name = secure_filename(file_obj.filename)
        if file_name:
            file_name = "%s-%s" % (job_id, file_name)
            file_path = os.path.join(job_dir, file_name)
            print(file_path)
            file_obj.save(file_path)
            storage_dict[key] = url_for("job_file", filename=file_name)
    return storage_dict

def save_options(form_dict, job_id, file_dict, job_dir):
    """ Save options as JSON file """
    job_opts = dict(form_dict)
    job_opts.update(file_dict)
    job_json_name = "%s-config.json" % job_id
    job_json_path = os.path.join(job_dir, job_json_name)
    with open(job_json_path, "wt") as json_file:
        json.dump(job_opts, json_file)
    return job_json_name

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
    id_str = "%s" % _time
    period = id_str.find(".")
    _id = "%s%s" % (id_str[:period], id_str[(period+1):(period+2)])
    print(_time, _id)
    return _id
