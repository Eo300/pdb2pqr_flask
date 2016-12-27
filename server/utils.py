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
from flask import url_for, render_template

PDB2PKA_OPTS = {'output_dir': 'pdb2pka_output',
                'clean_output': True,
                'pdie': 8,
                'sdie': 80,
                'pairene': 1.0}


class WebOptionsError(Exception):
    """ Errors that are specific to parsing web options """
    pass


class WebOptions:
    """ Web options from PDB2PQR server """

    def __init__(self, form_dict, file_dict):
        """ Initialize with request.form and request.files """
        self.form_dict = form_dict
        self.file_dict = file_dict
        self.run_options = {}
        self.force_field = None
        self.pdb_file = None
        self.pqr_file = None
        self.generate_apbs = None
        self.whitespace = None
        self.check_options()

    def check_optimization(self):
        """ Check optimization options """
        self.run_options["debump"] = self.form_dict.get("DEBUMP", False)
        self.run_options["opt"] = self.form_dict.get("OPT", False)

    def check_forcefield(self):
        """ Check forcefield options """
        self.ff = self.form_dict.get("FF").lower()
        userff_filename = self.file_dict.get("USERFF")
        if self.ff == 'user':
            if userff_filename:
                self.run_options["userff"] = userff_filename
            else:
                errstr = "Must provide user forcefield for parameter assignment."
                raise WebOptionsError(errstr)
        self.run_options["usernames"] = self.file_dict.get("USERNAMES")
        neutraln = self.form_dict.get("NEUTRALN", False)
        self.run_options["neutraln"] = neutraln
        neutralc = self.form_dict.get("NEUTRALC", False)
        self.run_options["neutralc"] = neutralc
        if (neutraln or neutralc) and (self.ff != "parse"):
            errstr = "You must use the PARSE forcefield for neutral N- or C-termini"
            raise WebOptionsError(errstr)
        self.run_options["ligand"] = self.file_dict.get("LIGAND", False)
        # TODO - may need to deal with CRLF issues in file parsing

    def check_structure(self):
        """ Check structure options """
        pdb_source = self.form_dict.get("PDBSOURCE")
        pdb_id = self.form_dict.get("PDBID")
        self.pdb_file = self.file_dict.get("PDB")
        if pdb_source == "ID":
            if pdb_id:
                errstr = "Want to fetch %s but..." % pdb_id
                errstr = errstr + " Nathan needs to implement." 
                raise NotImplementedError(errstr)
            else:
                errstr = "Need to specify PDB ID."
                raise WebOptionsError(errstr)
        elif pdb_source == "UPLOAD":
            if not self.pdb_file:
                errstr = "Need to upload PDB file."
                raise WebOptionsError(errstr)
        else:
            raise WebOptionsError("Invalid PDB source (%s)", pdb_source)
        if self.pdb_file[-4:].lower() == ".pdb":
            self.pqr_file = "%s.pqr" % self.pdb_file[:-4]
        else:
            self.pqr_file = "%s.pqr" % self.pdb_file

    def check_ph(self):
        """ Check pH value """
        ph_value = self.form_dict.get("PH")
        try:
            ph_value = float(ph_value)
            assert(ph_value > 0)
            assert(ph_value < 14)
        except (ValueError, AssertionError):
            errstr = "pH value must be a float between 0 and 14.\n"
            errstr = errstr + "You entered '%s'" % self.form_dict.get("PH")
            raise WebOptionsError(errstr)
        self.run_options["ph"] = ph_value

    def check_pka(self):
        """ Check pKa calculation method options """
        pka_calcmethod = self.form_dict.get("PKACALCMETHOD")

        if pka_calcmethod == "none":
            pka_calcmethod = None
        else:
            self.check_ph()
        if pka_calcmethod == "propka":
            self.run_options["ph_calc_method"] = pka_calcmethod
            errstr = "Nathan needs to implement PROPKA options"
            raise NotImplementedError(errstr)
        elif pka_calcmethod == "pdb2pka":
            self.run_options["ph_calc_method"] = pka_calcmethod
            errstr = "Nathan needs to implement PDB2PKA options"
            self.run_options["ph_calc_options"] = PDB2PKA_OPTS

    def check_output(self):
        """ Check output-formatting options """
        self.generate_apbs = self.form_dict.get("INPUT", False)
        self.whitespace = self.form_dict.get("WHITESPACE", False)
        self.run_options["ffout"] = self.form_dict.get("FFOUT")
        self.run_options["chain"] = self.form_dict.get("CHAIN", False)
        self.run_options["typemap"] = self.form_dict.get("TYPEMAP", False)
        self.run_options["drop_water"] = self.form_dict.get("DROPWATER", False)
        self.run_options['verbose'] = True
        self.run_options['selectedExtensions'] = ['summary']

    def check_options(self):
        """ Check input PDB2PQR options.  This is modeled after the old PDB2PQR WebOptions code at
        https://github.com/Electrostatics/apbs-pdb2pqr/blob/master/pdb2pqr/main_cgi.py#L179 """
        self.check_optimization()
        self.check_forcefield()
        self.check_structure()
        self.check_pka()
        self.check_output()

    def save_json(self, job_id=None, job_dir=None):
        """ Return the object contents as JSON.  If the job ID and directory are given, it will also
        save the JSON to file. """
        json_str = json.dumps(vars(self), sort_keys=True, indent=4)
        if job_id and job_dir:
            job_json_name = "%s-config.json" % job_id
            job_json_path = os.path.join(job_dir, job_json_name)
            with open(job_json_path, "wt") as json_file:
                json_file.write(json_str + "\n")
        return json_str


def store_uploads(file_dict, job_id, job_dir):
    """ Store uploaded files """
    storage_dict = {}
    for key, file_obj in file_dict.items():
        file_name = secure_filename(file_obj.filename)
        if file_name:
            file_name = "%s-%s" % (job_id, file_name)
            file_path = os.path.join(job_dir, file_name)
            file_obj.save(file_path)
            storage_dict[key] = url_for("job_file", filename=file_name)
    return storage_dict



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
    _id = "%s%s" % (id_str[:period], id_str[(period + 1):(period + 2)])
    print(_time, _id)
    return _id


def generic_error(e, code=None):
    """ A generic handler for web page errors """
    return render_template("error.html", error=e), code
