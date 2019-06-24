:title: Architecture

.. _architecture:

Architecture
============

.. contents:: Table of Contents
    :local:

PiedPiper is designed around the concept of pipes. Each phase in the CI/CD
pipeline is considered a ``pipe``. Each ``pipe`` has its own configuration
options, runtime environment, and invocation. PiedPiper's main configuration
interface is available through YAML files inside of the ``piedpiper.d/``
directory, which lives in your software project's repository.

The architecture of PiedPiper is split into two main components:
  - The `PiCli`_ client and
  - the `remote functions`_ which perform the pipe execution


PiCli
*****

The PiedPiper client. This component handles all user interaction with the system and is the
main entrypoint to the execution environment. PiCli will read through user-defined variables
in the ``piedpiper.d/`` directory and create various ``run_vars`` configuration objects. These
``run_vars`` define how PiCli will be executing the pipes and even which pipes get executed.


Remote Functions
****************

The remote functions are the meat-and-potatoes behind PiedPiper. Our current implementation utilizes
OpenFaaS, a Functions-as-a-Service framework, to orchestrate our PiedPiper pipeline execution jobs.
Each component that needs to be executed will make a call to an OpenFaaS function and return the results
of that run. 

Some examples of these remote functions are:
  - https://github.com/AFCYBER-DREAM/piedpiper-validator-faas
  - https://github.com/AFCYBER-DREAM/piedpiper-flake8-faas
  - https://github.com/AFCYBER-DREAM/piedpiper-cpplint-faas

These functions serve as an HTTP API wrapper around the chosen tool. The goal of PiedPiper is simply wrap
these external tools and return all output. We do not want to get in the way of developers and their normal
interactions with these popular tools.

The validation function, however, is special. This function provides the mechanism for validating CI configurations via
another Git repository. For more information on how this function works please see the `README`_

.. _README: https://github.com/AFCYBER-DREAM/piedpiper-validator-faas/blob/master/README.md


OpenFaaS
********

OpenFaaS is an integral component to PiedPiper because of its role in hosting the remote functions
which PiCli calls. While OpenFaaS itself isn't a requirement, something must act as a remote execution
environment which implements an API that PiedPiper expects. This definition of this API and the
requests and response which PiCli expects can be found in the `PiedPiper API`_ section.


PiedPiper API
*************

PiedPiper's client and remote functions must pass data to each other over a defined API. Currently, PiedPiper
uses a ZIP file containing both the project source files to lint/test/build and a YAML file called ``run_vars.yml``.
This ``run_vars`` file contains the configuration and specification of the remote execute job.

For more information on the definition of the ``run_vars.yml`` file please see the :ref:`api documentation<api>`

Directory Structure
*******************

.. code-block:: bash

  piedpiper.d
  ├── default_vars.d
  │   ├── file_vars.d
  │   │   └── src_config.yml
  │   ├── group_vars.d
  │   │   ├── all.yml
  │   │   └── python_lint.yml
  │   └── pipe_vars.d
  │       ├── pi_sast.yml
  │       ├── pi_style.yml
  │       └── pi_validate.yml
  └── pi_global_vars.yml


pi_global_vars.yml
------------------

PiedPiper's main configuration is controlled via it ``pi_global_vars.yml``
file. This file contains configuration options which are not tied to 
a specific pipe, file, or group.

**vars_dir**
  This configuration option controls the piedpiper variable directory.
  By default this is set to ``default_vars.d``, but can be configured to be 
  any direct child directory under ``piedpiper.d``. 
  The intention of this directory is to allow developers to create a clone of 
  the Piedpiper configuration to test various variable changes or different 
  versions of its pipelines without modifying the production variables.

**ci_provider**
  This configuration option informs PiedPiper what CI provider is being used.
  PiCli will then read the CI-provider configuration file and pass its 
  configuration to the validation function (if enabled). 
  At the moment we only support Gitlab-CI so the ``.gitlab-ci.yml``
  file is the only thing being passed to the validator function.

**version**
  This option specifies the version of PiedPiper that is being used. 
  PiedPiper is version controlled so that repeatable CI builds are possible.


default_vars.d/
---------------

This directory contains the default configuration files for PiedPiper.

default_vars.d/group_vars.d/
----------------------------

This directory contains group-specific configurations for pipelines.
Each file in this directory is considered a "group" and will be fed into 
PiedPiper as a "run." By default, we provide an ``all.yml`` file which 
defines a ``noop`` operation for every pipeline that PiedPiper manages.

This is the default ``all.yml`` file which is provided when bootstraping
a project with PiedPiper

.. code-block:: yaml

  ---
  pi_style:
    - name: "*"
      styler: "noop"
  pi_sast:
    - name: "*"
      sast: "noop"

This default group will apply the ``noop`` styler and SAST configurations to all
files in the directory. By doing this we ensure that a brand-new project pass the
PiedPiper Pipeline and that every file is accounted for, even if that file is
passed to a ``noop`` function.

default_vars.d/file_vars.d/
---------------------------

This directory contains file overrides for groups defined in 
``default_vars.d/group_vars.d/``. The intention is to give the developer a way
to exclude specific files from Pipeline runs. 
For example, if the developer was required to include a third-party 
Python library as an actual file in their repository, they could specify 
the following in a ``default_vars.d/files_vars.d/third_party_file.yml`` file
to exclude that file from the Linting pipeline.

.. code-block:: yaml

  ---
  file: "src/third_party_file.py"
  styler: "noop"


default_vars.d/pipe_vars.d/
---------------------------

This directory contains pipe-specific configurations. Every pipe will contain 
a base-level configuration, and some pipes may expand on that configuration 
and require additional configuration options. Every ``pipe_vars.d`` file must 
contain a YAML dictionary named after the pipe in the following style: 
``pi_{STEP}_pipe_vars``. 
The required configuration of each step's pipe_vars can be found 
in ``model/{PIPE}_pipeconfig_schema.py``

Here is an example pipe_vars.d configuration file

.. code-block:: yaml

  ---
  pi_style_pipe_vars:
    run_pipe: true
    version: latest
    url: http://172.17.0.1:8080/function

**run_pipe**
  Controls whether the pipe will be ran when ``picli`` is called. 
  This variable can be enforced by the ``validation`` PiCli step.

**version**
  The version of the pipe function to use. 
  This corresponds to a function URL
  I.E. ``http://172.17.0.1:8080/function/piedpiper-flake8-function-0-0-1``
  A version of ``latest`` will simply refer to 
  ``http://172/17.0.1:8080/function/piedpiper-flake8-function``

**url**
  The baseurl to use when invoking the function. 
  Every step will build this URL itself based on the step name, so this URL 
  will basically control the OpenFaaS entrypoint to its functions.
