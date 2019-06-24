:title: Configuration

.. _configuration:

Configuration
=============

.. contents:: Table of Contents
    :local:


PiCli configuration is all handled through YAML files located in ``piedpiper.d`` inside
the project root directory. These files are meant to be highly configurable and well documented,
but are also meant to provide a set of sensible defaults so that they don't have to be
messed with unless you really want to.

Configuring groups
******************

A "group" in PiCli is a grouping of files which will make up a run, or execution. Let's take
a look at the default ``all`` group located in ``piedpiper.d/default_vars.d/group_vars.d/all.yml``

.. code-block:: yaml

  ---
  pi_style:
    - name: "*"
      styler: noop
  pi_sast:
    - name: "*"
      sast: noop

Here we have one group defined, ``all``. This group configuration file sets the `styler` of `noop` for all
files in the project root directory. It also sets the `sast` of `noop` for all files in the project root directory.

The ``all`` group is special. It will be read first by PiCli meaning it will be providing the defaults for
your respository. It is suggested that you do not modify the all group unless you know what you are doing.
If you wish to define other values for different file globs in your repository, then it is suggested
that you create additional group files under ``piedpiper.d/default_vars.d/group_vars.d/``. 

Here is an example of a second group located in a ``python_lint.yml`` file.

.. code-block:: yaml

  ---
  pi_style:
    - name: "*.py"
      styler: flake8

This second group represents an override. Any additional group after ``all.yml`` will override the values of previous
file globs. In this example, we are overriding the default action of ``noop`` for ``*``, or all files, with 
``flake8`` for ``*.py`` files, or all python files. This tells PiCli to send all files ending in ``.py`` in your 
repository to the ``flake8`` function. All other files will be sent to the ``noop`` function, aka, do nothing.

Overriding specific files
*************************

You can also override specific files through the ``file_vars.d/`` directory. All YAML files located in this
directory will be scanned by PiCli and read. If the file definition matches the spec it will be merged into 
the run configuration last. This means that file definitions located in ``file_vars.d/`` will have precedence over
files specified by file globs in ``group_vars.d/``. This functionality was inspired by ``Ansible`` and its group_vars
and host_vars.

In this example we have been given a file by a third-party. We must include this file in our repository directly
because of our customer-driven requirements. However, we do not want to lint this file because we do not have
control over modifications to this file. We simply must live with whatever horribly (or amazing) style choices were 
made when this third-party file was created.

To do this, we create a file in ``file_vars.d/src_config.yml`` with an arbitrary name. We, then, create the following
definition for the file inside of this newly created file:

.. code-block:: yaml

  ---
  file: "src/config.py"
  styler: "noop"

We must specify the file and any overrides we have for that particular file. This definition will override our 
previously configured definition for ``*.py``, or all python files.

This file will be excluded from the ``flake8`` linter function and will instead of sent to the ``noop`` function.


Enable and Disabling steps
**************************

PiCli was meant to be modular. You should be able to run specific steps by calling those in the cli, but you
should also be able to define which steps are ran through the configuration files.

Pipe configurations are made in the ``piedpiper.d/default_vars.d/pipe_vars.d/`` directory. Each step, or pipe, will
have its own configuration file in YAML.

For example, let's say we want to disable the validation pipe just for local execution. We would go into
``piedpiper.d/default_vars.d/pipe_vars.d/`` and change ``run_pipe: True`` to ``run_pipe: False``

.. code-block:: yaml

  ---
  pi_validate_pipe_vars:
    run_pipe: False
    url: http://172.17.0.1:8080/function
    version: latest
    policy:
      enabled: True
      enforcing: True
      version: 0.0.0

.. note:: We could also change the policy setting to false, or enforcing to false. See the `Validation`_ section for more details


Validation
**********

Validation is an important part of PiedPiper. The validation step will parse your PiedPiper configuration files 
under ``piedpiper.d/`` and your ``ci_provider`` configuration file and send 
that data off to a validation function. That validation function will then ensure that your pipeline adheres to 
whatever standard is set for your project. This pipeline standard is held in an external Git repository and is meant 
to be configured by a team lead or Technical Director. 

The validation step is meant to ensure that your pipeline is calling the required stages with the required options 
based on your project's requirements.

Let's take an example Python project. Your team lead has decided that all code must be linted. There isn't any 
direction on what linting tool should be used or what standard should be followed, but the code must have a lint step. 
As a developer, you want to ensure your code will pass the defined standard before you make a commit to the repository. 
So you make your changes, fire up PiCli and call the ``lint`` step.

.. code-block:: bash

  ± % picli lint
  --> Action: Validate
  ERROR: [
      {
          "ci": {
              "errors": [
                  {
                      "include": {
                          "errors": false
                      }
                  },
                  {
                      "stages": {
                          "errors": "{'stages': [ValueError(\"Stages must include validate. You passed ['build', 'generate_docker_image_push_to_nexus']\"), ValueError(\"Stages must include lint. You passed ['build', 'generate_docker_image_push_to_nexus']\")]}"
                      }
                  }
              ]
          }
      }
  ]

PiCli will validate your ``.gitlab-ci.yml`` file to ensure that your pipeline is calling the appropriate stages. 
Since our team lead has configured the validation repository to enforce the ``lint`` step we must include this step 
in our ``.gitlab-ci.yml`` file. After making the appropriate modifications we run the lint step again.

.. code-block:: bash

  ± % picli lint
  --> Action: Validate
  Validation completed successfully.
  --> Action: Style
  --> Executing styler noop
  Executing noop on piedpiper.d/pi_global_vars.yml
  Executing noop on piedpiper.d/default_vars.d/pipe_vars.d/pi_validate.yml
  Executing noop on piedpiper.d/default_vars.d/pipe_vars.d/pi_sast.yml
  Executing noop on piedpiper.d/default_vars.d/pipe_vars.d/pi_style.yml
  Executing noop on piedpiper.d/default_vars.d/file_vars.d/src_config.yml
  Executing noop on piedpiper.d/default_vars.d/group_vars.d/python_lint.yml
  Executing noop on piedpiper.d/default_vars.d/group_vars.d/all.yml
  Executing noop on piedpiper.d/test_vars.d/pipe_vars.d/pi_validate.yml
  Executing noop on piedpiper.d/test_vars.d/pipe_vars.d/pi_sast.yml
  Executing noop on piedpiper.d/test_vars.d/pipe_vars.d/pi_style.yml
  Executing noop on piedpiper.d/test_vars.d/file_vars.d/src_config.yml
  Executing noop on piedpiper.d/test_vars.d/group_vars.d/all.yml
  Executing noop on charon/functional.py
  Executing noop on charon/scanner.py
  Executing noop on charon/worker.py
  Executing noop on charon/cloud.py
  Executing noop on charon/config.py
  Executing noop on charon/__init__.py
  --> Action: Sast
  --> Executing SAST analyzer: noop
  Executing noop on piedpiper.d/pi_global_vars.yml
  Executing noop on piedpiper.d/default_vars.d/pipe_vars.d/pi_validate.yml
  Executing noop on piedpiper.d/default_vars.d/pipe_vars.d/pi_sast.yml
  Executing noop on piedpiper.d/default_vars.d/pipe_vars.d/pi_style.yml
  Executing noop on piedpiper.d/default_vars.d/file_vars.d/src_config.yml
  Executing noop on piedpiper.d/default_vars.d/group_vars.d/python_lint.yml
  Executing noop on piedpiper.d/default_vars.d/group_vars.d/all.yml
  Executing noop on piedpiper.d/test_vars.d/pipe_vars.d/pi_validate.yml
  Executing noop on piedpiper.d/test_vars.d/pipe_vars.d/pi_sast.yml
  Executing noop on piedpiper.d/test_vars.d/pipe_vars.d/pi_style.yml
  Executing noop on piedpiper.d/test_vars.d/file_vars.d/src_config.yml
  Executing noop on piedpiper.d/test_vars.d/group_vars.d/all.yml
  Executing noop on charon/functional.py
  Executing noop on charon/scanner.py
  Executing noop on charon/worker.py
  Executing noop on charon/cloud.py
  Executing noop on charon/config.py
  Executing noop on charon/__init__.py

Well it looks like everything was accounted for. Except nothing was actually linted! We need to define our linting 
tool and which files that tool will take into account.

First we add a new file ``piedpiper.d/default_vars.d/group_vars.d/python_lint.yml``

Then we add the following contents to that file

.. code-block:: yaml

  ---
  pi_style:
    - name: "*.py"
      styler: flake8
  pi_sast:
    - name: "*"
      sast: noop

We don't currently support SAST for Python so we just ``noop`` those. After running ``picli lint`` again, we will get 
our flake8 results.


Supported Pipes
***************

+------------+------------+-----------+---------+----------+----------+
| Language   |   Style    |   SAST    |   Unit  |   Build  |   DAST   |
+============+============+===========+=========+==========+==========+
|   Python   |  flake8    |   None    |  None   |   None   |   None   |
+------------+------------+-----------+---------+----------+----------+
|    C++     |  cpplint   |  cppcheck |  None   |   None   |   None   |
+------------+------------+-----------+---------+----------+----------+
