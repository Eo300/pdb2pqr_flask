# A Flask version of the PDB2PQR server

This is an attempt to port the [PDB2PQR web server](http://www.poissonboltzmann.org) to [Flask](http://flask.pocoo.org/) to simplify the code base and make it easier to port to cloud services.
This particular code was shamelessly <strike>ripped off from</strike> modeled after the [Flask examples](http://flask.pocoo.org/).

The code is not functional and is intended as a prototype.  Here are the current steps to get it "working" (assuming a Bash environment); a [virtualenv](https://virtualenv.pypa.io/en/stable/) is strongly recommended.

```
pip install --editable .
export FLASK_APP=server
export FLASK_DEBUG=1
python -m flask setup
python -m flask run
```

Point your browser to <http://127.0.0.1:5000/> and hope for the best!
