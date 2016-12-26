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
        self.check_options()

    def check_optimization(self):
        """ Check optimization options """
        self.run_options["debump"] = ("DEBUMP" in self.form_dict)
        self.run_options["opt"] = ("OPT" in self.form_dict)

    def check_forcefield(self):
        """ Check forcefield options """
        self.ff = self.form_dict.get("FF").lower()

    def check_structure(self):
        """ Check structure options """
        pdb_source = self.form_dict[""].get("PDBSOURCE")
        if pdb_source == "ID":
            pdb_id = self.form_dict["PDBID"]
            self.pdb_file = get_pdb_url(pdb_id)
        elif pdb_source == "UPLOAD":
            print(self.file_dict)
            self.pdb_file = self.file_dict["PDB"]
            self.pdb_file = self.file_dict.get("FOO")
        else:
            raise WebOptionsError("Invalid PDB source (%s)", pdb_source)

    def check_options(self):
        """ Check input PDB2PQR options.  This is modeled after the old PDB2PQR
        WebOptions code at
        https://github.com/Electrostatics/apbs-pdb2pqr/blob/master/pdb2pqr/main_cgi.py#L179 """
        print(self.form_dict)
        self.check_optimization()
        print(self.run_options)
        self.check_forcefield()
        self.check_structure()

    # else:
    #     raise WebOptionsError('You need to specify a pdb ID or upload a pdb file.')
        
    # if form.has_key("PKACALCMETHOD"):
    #     if form["PKACALCMETHOD"].value != 'none':
    #         if not form.has_key('PH'):
    #             raise WebOptionsError('Please provide a pH value.')
            
    #         phHelp = 'Please choose a pH between 0.0 and 14.0.'
    #         try:
    #             ph = float(form["PH"].value)
    #         except ValueError:
    #             raise WebOptionsError('The pH value provided must be a number!  ' + phHelp)
    #         if ph < 0.0 or ph > 14.0: 
    #             text = "The entered pH of %.2f is invalid!  " % ph
    #             text += phHelp
    #             raise WebOptionsError(text)
    #         self.runoptions['ph'] = ph
    #         #build propka and pdb2pka options
    #         if form['PKACALCMETHOD'].value == 'propka':
    #             self.runoptions['ph_calc_method'] = 'propka'
    #             self.runoptions['ph_calc_options'] = utilities.createPropkaOptions(ph, False)
    #         if form['PKACALCMETHOD'].value == 'pdb2pka':
    #             self.runoptions['ph_calc_method'] = 'pdb2pka'
    #             self.runoptions['ph_calc_options'] = {'output_dir': 'pdb2pka_output',
    #                                                   'clean_output': True,
    #                                                   'pdie': 8,
    #                                                   'sdie': 80,
    #                                                   'pairene': 1.0}
             
    # self.otheroptions['apbs'] = form.has_key("INPUT")
    # self.otheroptions['whitespace'] = form.has_key("WHITESPACE")
    
    # if self.ff == 'user':
    #     if form.has_key("USERFF") and form["USERFF"].filename:
    #         self.userfffilename = sanitizeFileName(form["USERFF"].filename)
    #         self.userffstring = form["USERFF"].value
    #         self.runoptions['userff'] = StringIO(form["USERFF"].value)
    #     else:
    #         text = "A force field file must be provided if using a user created force field."
    #         raise WebOptionsError(text)
            
    #     if form.has_key("USERNAMES") and form["USERNAMES"].filename:
    #         self.usernamesfilename = sanitizeFileName(form["USERNAMES"].filename)
    #         self.usernamesstring = form["USERNAMES"].value
    #         self.runoptions['usernames'] = StringIO(form["USERNAMES"].value)
    #     else:
    #         text = "A names file must be provided if using a user created force field."
    #         raise WebOptionsError(text)
        
    # if form.has_key("FFOUT") and form["FFOUT"].value != "internal":
    #     self.runoptions['ffout'] = form["FFOUT"].value
            
    # self.runoptions['chain'] = form.has_key("CHAIN")
    # self.runoptions['typemap'] = form.has_key("TYPEMAP")
    # self.runoptions['neutraln'] = form.has_key("NEUTRALN")
    # self.runoptions['neutralc'] = form.has_key("NEUTRALC")
    # self.runoptions['drop_water'] = form.has_key("DROPWATER")
    
    # if (self.runoptions['neutraln'] or self.runoptions['neutraln']) and \
    #     self.ff != 'parse':
    #     raise WebOptionsError('Neutral N-terminus and C-terminus require the PARSE forcefield.')
    
    # if form.has_key("LIGAND") and form['LIGAND'].filename:
    #     self.ligandfilename=sanitizeFileName(form["LIGAND"].filename)
    #     ligandfilestring = form["LIGAND"].value
    #     # for Windows and Mac style newline compatibility for pdb2pka
    #     ligandfilestring = ligandfilestring.replace('\r\n', '\n')
    #     self.ligandfilestring = ligandfilestring.replace('\r', '\n')
        
    #     self.runoptions['ligand'] = StringIO(self.ligandfilestring)
        
    # if self.pdbfilename[-4:]==".pdb":
    #     self.pqrfilename = "%s.pqr" % self.pdbfilename[:-4]
    # else:
    #     self.pqrfilename = "%s.pqr" % self.pdbfilename
        
    # #Always turn on summary and verbose.
    # self.runoptions['verbose'] = True
    # self.runoptions['selectedExtensions'] = ['summary']

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


def generic_error(e, code=None):
    """ A generic handler for web page errors """
    return render_template("error.html", error=e), code
