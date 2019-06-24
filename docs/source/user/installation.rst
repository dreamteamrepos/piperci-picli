:title: Installation

.. _installation:

Installation
============

.. contents:: Table of Contents
    :local:

PiCli has two supported installation methods, Pip and Docker. PiCli is supported on
both Windows and Linux based operating systems. If you run into issues please open
a `bug report`_

.. _`bug report`: https://github.com/AFCYBER-DREAM/piedpiper-picli/issues

Pip
***

Prerequisites
-------------
* Python 3.7
* pip
* virtualenv

Ensure virtualenv is installed. This is usually done through your system's package
manager but can also be done through pip itself.

**Ubuntu/Debian**

.. code-block:: bash

  sudo apt-get install -y virtualenv

**RedHat/CentOS**

.. code-block:: bash

  sudo yum install -y python-virtualenv

**Pip**

.. code-block:: bash

  sudo pip install virtualenv

Installing PiCli into a virtualenv
----------------------------------

Ensure that python3.7 is installed, then create a new virtualenv using python3.7

.. code-block:: bash

  virtualenv -p python3.7 picli

Next activate your virtualenv

.. code-block:: bash

  source picli/bin/activate

.. note::

  If you are on windows you will run ``./picli/Scripts/activate.bat``


Docker
******

Prerequisites
-------------

* Docker

To run the client from a Docker container with access to your current working directory, do the following:

.. code-block:: bash

  $ docker run -v $(pwd):/code -it piedpiper-picli:latest /bin/sh
  # cd /code
  # picli --help
  /code # picli --help
  Usage: picli [OPTIONS] COMMAND [ARGS]...

  Options:
    -c, --config TEXT  The PiCli configuration file to use
    --debug            Enable debug logging
    --help             Show this message and exit.

  Commands:
    lint      Command used to execute the "lint" container found in...
    sast
    style
    validate


