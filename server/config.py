# -*- coding: utf-8 -*-
"""
    A Flask version of the PDB2PQR server
    ~~~~~~~~

    Configuring the PDB2PQR server

    :copyright: (c) 2016 Battelle, etc.
    :license: BSD, see LICENSE for more details.
"""
import os
import os.path

# Job directory
JOBS_DIR = os.path.normpath("./tmp")
# Debug status
DEBUG = True
# PDB2PQR version number (should be replaced automatically)
# TODO - replace this with auto-configured version number
PDB2PQR_VERSION = "13.666"
