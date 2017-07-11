# Overview

[TODO]

# Requirements
* Python 3.5.1 or higher
* dill 0.2.6. or higher (https://pypi.python.org/pypi/dill)
* Compatible embedded client.
    * [Reference implementation for 6.S08's Teensy-based system](https://github.com/dmendelsohn/micrograder-teensy/)

# Setup
* Just clone the repo!  The shell commands in this document should be executed from the
top level directory.
* You'll need to change the `ADDR` variable in `communication.py` to the correct port
for USB serial communication.

# Usage
* There are two relevant "file types": Log files and TestCase files.  These
are truly separate types, since they're both just pickled Python objects (
of types RequestLog and TestCase respectively).  Typically, I use the
extension ".log" for Log files and put them in host/resources/logs/, and I use
the extension ".tc" for TestCase files and put them in host/resources/cases/.
Neither of these practices is required.
* TODO

# Architecture
...