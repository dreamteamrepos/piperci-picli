.. _intro:

Introduction to PiedPiper
=========================

PiedPiper is a managed pipeline validation and execution framework. PiedPiper gives the developer tools to
ensure all changes are validated against the same infrastructure that is enforced by the CI/CD pipeline and
enables managerial entities to programmatically enforce specific pipeline steps and configurations for each project
that they oversee.

The intention is to give developers the ability to quickly bootstrap a project with a set of pipeline configurations 
that will run through the full pipeline. 

The ``picli`` is the entrypoint to PiedPiper. It is the common interface into the CI/CD systems that are managed and
is expected to be used by both the developer and CI platforms.

.. note::
    To find more information on the architecture of PiedPiper see the :ref:`Architecture Guide<architecture>`.


