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
* There are two relevant "file types": log files and testcase files.  These
are truly separate types, since they're both just pickled Python objects (
of types RequestLog and TestCase respectively).  Typically, I use the
extension ".log" for log files and put them in host/resources/logs/, and I use
the extension ".tc" for testcase files and put them in host/resources/cases/.
Neither of these practices is required.

## Assessing
* To use a particular testcase file to assess an embedded system, run:

`python -m src assess --testcase path/to/testcase [--log path/to/save/log]`

* If the --log option is specified, a log will be saved at that path.

## Recording
* To record the actions of a system (presumeably running in RECORD mode),
without performing any assessmenet, run:

`python -m src record --log path/to/save/log`

* To stop recording, simply unplug the embedded system.  The log file will be
saved at the specified path.

## Constructing new test cases
* You can manually create TestCase objects, though you'll have to be pretty
familiar with the system to do so.  Just save those objects using dill (an
improvement on Python's `pickle` module).
* You can create a TestCase from an existing log automatically.  To do so, run:

`python -m construct --log path/to/log --testcase path/to/save/testcase`

* It is also possible to create a multi-Frame TestCase (learn more below).
For example, create a 2-Frame TestCase by running:

`python -m construct --log path/to/log --testcase path/to/save/testcase -n 2`

* By default, Frames end when a Wifi request occurs, and the next frame begins when
the subsequent Wifi response comes in.  The first Frame begins with a "Start" Print statement,
and the last Frame ends whenever the latest timestamp in the log occurred.

# Architecture
* TODO