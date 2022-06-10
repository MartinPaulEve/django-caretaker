# Changelog

## Since Last Release
* Added sphinx documentation
* Added docstrings and documentation

## 0.3.1: “Tricorder” (2022-06-08)
* Rename settings variables to include CARETAKER prefix
* Allow for multiple backend providers
* Move web view to use abstracted backends
* Add annotations to all main methods by @MartinPaulEve

## 0.2.0: “Ocampa” (2022-06-07)
* Expose command-line arguments for additional paths and add settings configuration option

## 0.1.4: “Array” (2022-06-06)
First functional version.

This is the first release of django-caretaker. This minor increment fixes unit tests and removes relative imports from the testing framework.

* Generation of Terraform configuration files to provision S3 bucket
* Automatic installation of crontab entry for daily backups
* Push/pull/list backup versions
* Automatic packing of media directory
* Automatic packing of data.json from dumpdata command
* Basic administrative view of and urlconfig for backups (caretaker.urls)
* Full test suite coverage