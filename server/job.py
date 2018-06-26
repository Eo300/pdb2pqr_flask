# -*- coding: utf-8 -*-
"""
    A Flask version of the PDB2PQR server
    ~~~~~~~~

    A job on the PDB2PQR server

    :copyright: (c) 2016 Battelle, etc.
    :license: BSD, see LICENSE for more details.
"""
import os.path
import json
import urllib
from werkzeug.utils import secure_filename
from flask import url_for, render_template
from . import utils

PDB2PKA_OPTS = {'output_dir': 'pdb2pka_output',
                'clean_output': True,
                'pdie': 8,
                'sdie': 80,
                'pairene': 1.0}

STATUS_RUNNING = "Running";
STATUS_DIED = "Dead";
STATUS_FINISHED = "Finished";


class JobError(Exception):
    """ Errors that are specific to parsing web options """
    pass


class Job:
    """ Web options from PDB2PQR server """
    def __init__(self, req_form, req_files, tmp_path):
        """ Initialize with request.form and request.files.   """
        self.tmp_path = tmp_path
        self.job_id = utils.set_job_id()
        self.req_form = req_form
        self.req_files = req_files
        self.file_dict = {}
        self.run_options = {}
        self.force_field = None
        self.pdb_file = None
        self.pqr_file = None
        self.generate_apbs = None
        self.whitespace = None
        self.store_uploads()
        self.check_options()

    def check_optimization(self):
        """ Check optimization options """
        self.run_options["debump"] = self.req_form.get("DEBUMP", False)
        self.run_options["opt"] = self.req_form.get("OPT", False)

    def check_forcefield(self):
        """ Check forcefield options """
        self.force_field = self.req_form.get("FF").lower()
        userff_filename = self.file_dict.get("USERFF")
        if self.force_field == 'user':
            if userff_filename:
                self.run_options["userff"] = userff_filename
            else:
                errstr = "Must provide user forcefield for parameter assignment."
                raise JobError(errstr)
        self.run_options["usernames"] = self.file_dict.get("USERNAMES")
        neutraln = self.req_form.get("NEUTRALN", False)
        self.run_options["neutraln"] = neutraln
        neutralc = self.req_form.get("NEUTRALC", False)
        self.run_options["neutralc"] = neutralc
        if (neutraln or neutralc) and (self.force_field != "parse"):
            errstr = "You must use the PARSE forcefield for neutral N- or C-termini"
            raise JobError(errstr)
        self.run_options["ligand"] = self.file_dict.get("LIGAND", False)
        # TODO - may need to deal with CRLF issues in file parsing

    def check_structure(self):
        """ Check structure options """
        pdb_source = self.req_form.get("PDBSOURCE")
        pdb_id = self.req_form.get("PDBID")
        self.pdb_file = self.file_dict.get("PDB")
        if pdb_source == "ID":
            if pdb_id:
                pdb_success = self.download_pdb()
                if not pdb_success:
                    errstr = "Please specify a valid PDB ID"
                    raise JobError(errstr)
                self.pdb_file = self.file_dict.get("PDB")
            else:
                errstr = "Need to specify PDB ID."
                raise JobError(errstr)
        elif pdb_source == "UPLOAD":
            if not self.pdb_file:
                errstr = "Need to upload PDB file."
                raise JobError(errstr)
        else:
            raise JobError("Invalid PDB source (%s)", pdb_source)
        if self.pdb_file[-4:].lower() == ".pdb":
            self.pqr_file = "%s.pqr" % self.pdb_file[:-4]
        else:
            self.pqr_file = "%s.pqr" % self.pdb_file

    def check_ph(self):
        """ Check pH value """
        ph_value = self.req_form.get("PH")
        try:
            ph_value = float(ph_value)
            assert(ph_value > 0)
            assert(ph_value < 14)
        except (ValueError, AssertionError):
            errstr = "pH value must be a float between 0 and 14.\n"
            errstr = errstr + "You entered '%s'" % self.req_form.get("PH")
            raise JobError(errstr)
        self.run_options["ph"] = ph_value

    def check_pka(self):
        """ Check pKa calculation method options """
        pka_calcmethod = self.req_form.get("PKACALCMETHOD")

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
        self.generate_apbs = self.req_form.get("INPUT", False)
        self.whitespace = self.req_form.get("WHITESPACE", False)
        self.run_options["ffout"] = self.req_form.get("FFOUT")
        self.run_options["chain"] = self.req_form.get("CHAIN", False)
        self.run_options["typemap"] = self.req_form.get("TYPEMAP", False)
        self.run_options["drop_water"] = self.req_form.get("DROPWATER", False)
        self.run_options['verbose'] = True
        self.run_options['selectedExtensions'] = ['summary']

    def check_options(self):
        """ Check input PDB2PQR options.  This is modeled after the old PDB2PQR Job code at
        https://github.com/Electrostatics/apbs-pdb2pqr/blob/master/pdb2pqr/main_cgi.py#L179 """
        self.check_optimization()
        self.check_forcefield()
        self.check_structure()
        self.check_pka()
        self.check_output()

    def save_json(self):
        """ Return the object contents as JSON.  If the job ID and directory are given, it will also
        save the JSON to file. """
        json_dict = vars(self)
        del(json_dict["req_files"])
        json_str = json.dumps(vars(self), indent=4, sort_keys=True)
        job_json_name = "%s-config.json" % self.job_id
        job_json_path = os.path.join(utils.local_job_dir(tmp_path=self.tmp_path, job_id=self.job_id),
                                     job_json_name)
        with open(job_json_path, "wt") as json_file:
            json_file.write(json_str + "\n")
        return json_str

    def store_uploads(self):
        """ Store the uploaded files """
        self.file_dict = {}
        job_dir = utils.local_job_dir(job_id=self.job_id, tmp_path=self.tmp_path)
        for key, file_obj in self.req_files.items():
            file_name = secure_filename(file_obj.filename)
            if file_name:
                file_path = os.path.join(job_dir, file_name)
                file_obj.save(file_path)
            self.file_dict[key] = url_for("job_file", jobid=self.job_id, filename=file_name)

    def download_pdb(self):
        """ Download and stores the PDB file of the specified PDB ID """
        job_dir = utils.local_job_dir(job_id=self.job_id, tmp_path=self.tmp_path)
        pdb_id = self.req_form.get("PDBID")
        URLpath = "https://files.rcsb.org/download/" + pdb_id + ".pdb"
        try:
            fin_pdb = urllib.urlopen(URLpath)
            if fin_pdb.getcode() != 200 or 'nosuchfile' in fin_pdb.geturl():
                raise IOError
        except IOError:
            return None                
        
        file_name = pdb_id+".pdb"
        fout_pdb = open(job_dir + "/" + file_name, 'w')
        for line in fin_pdb:
            fout_pdb.write(line)
        fout_pdb.close()

        # Added to keep consistency with generated PQR file name
        self.file_dict["PDB"] = url_for("job_file", jobid=self.job_id, filename=file_name)
        return True