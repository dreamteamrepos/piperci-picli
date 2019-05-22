ToDo:
Document more things

# PiCli

PiCli is a python client for PiedPiper, a CI-pipeline validation framework.

Additional documentation for PiedPiper can be found here: (https://piedpiper-picli.readthedocs.io/en/latest/)

## Getting Started

A local development environment can be configured using the following Ansible collection: https://github.com/AFCYBER-DREAM/ansible-collection-pidev/

Follow these instructions to turn a new machine into a PiedPiper development environment:

```bash
# the "org" variable should be the name of your Github.com organization
org="afcyber-dream";

# the "repo" variable should be the name of the repo containing your fork of afcyber-dream/ansible-collection-pidev
repo="ansible-collection-pidev";

# the "env" variable should be the nickname of the environment you wish to provision
env="ubuntu1804/dockerswarm+openfaas"

# once you have set these three variables, run this command as `root` (not a sudo user):
bash <(curl -s https://raw.githubusercontent.com/${org}/${repo}/master/bootstrap.sh) ${org}/${repo} ${env}
```
Please refer to the README of that repository for further information.

### Prerequisites

* Python 3.6 7
* (Optionally) virtualenv  
* PiedPiper OpenFaaS functions installed. (See above)


### Installing

#### Docker Installation

```
docker build -t picli .
docker run -it picli /bin/sh
```

#### Python installation
```
python setup.py install
```

## Using

To run PiCli:

#### Execute a lint

```
picli run --stages=style --clean --wait
```

#### Execute a validation

```
picli run --stages=validate --clean --wait
```

### CLI Arguments

**debug**
```
picli --debug run
```
Debug will dump PiCli's run_vars to the screen during execution. This allows
the user to validate PiCli's configuration that is being sent to the
various functions. 

**run**
```
picli run
```
The main entrypoint to PiCli. This will execute the stages defined in your stages.yml file
by sending HTTP requests to the resources you have provided.

**display**
```
picli display
```
Display job results from the commandline. This will read your local state file for the taskID of each stage,
query GMan for job status, and then download artifacts for each job.

## Running the tests

To run the lint tests use tox: `tox -e lint`

To run the unit tests use tox: `tox -e unit`


## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags).

## Authors

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

TBD

## Acknowledgments

* Inspiration for the CLI framework came from the Ansible Molecule project

