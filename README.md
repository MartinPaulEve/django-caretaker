# django-caretaker
django-caretaker ('The Caretaker') is a Django app that backs up your database and media files to a versioned remote object store, such as an AWS S3 bucket. It comes with the Terraform files to provision the required cloud infrastructures (e.g. S3 bucket) and provides management commands to schedule regular backups.

![license](https://img.shields.io/github/license/martinpauleve/django-caretaker) ![activity](https://img.shields.io/github/last-commit/MartinPaulEve/django-caretaker) ![build status](https://github.com/MartinPaulEve/django-caretaker/actions/workflows/tests.yaml/badge.svg)

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)

[![asciicast](https://asciinema.org/a/HnqOncypouhiHcs4r2mZn0TRS.svg)](https://asciinema.org/a/HnqOncypouhiHcs4r2mZn0TRS)

## Install
To install the module, use pip:

    pip install django-caretaker

Add 'caretaker' to your installed apps in your Django settings file.

Add 'path('caretaker/', include('caretaker.urls')),' to your urls.py file to enable the /caretaker/list view.

## Setup and Configuration
### Configure a backend and access rights
django-caretaker has the ability to support multiple cloud-based object store backends. At the moment, we have support for either Amazon S3 or local storage.

#### Amazon S3 / IAM
Ensure that you have a working AWS cli client and configure it if not.

Set the BACKUP_BUCKET variable in your settings.py file. This must be a globally unique name for the S3 bucket. You should also set the MEDIA_ROOT folder so that we know what to back up:

    CARETAKER_BACKUP_BUCKET = 'caretakertestbackup'  # put the name of the backup instance here
    CARETAKER_ADDITIONAL_BACKUP_PATHS = ['/home/user/path1', '/home/user/path2']  # put additional paths to backup here
    CARETAKER_BACKEND = 'Amazon S3' # note that this is case sensitive
    CARETAKER_FRONTEND = 'Django'  # note that this is case sensitive
    MEDIA_ROOT = '/var/www/media'  # add your MEDIA ROOT to backup

The CARETAKER_BACKENDS list allows you to specify the available backends. The CARETAKER_BACKEND variable selects the backend to use (there is only S3 at the moment). The same is true of CARETAKER_FRONTENDS and CARETAKER_FRONTEND (which only support Django at the moment).

Generate and run Terraform configuration in your home directory:

    ./manage.py get_terraform --output-directory=~/terraform_configuration
    cd ~/terraform_configuration
    terraform init
    terraform apply
    terraform output --json

Note down the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and put them in your settings.py file:

    AWS_ACCESS_KEY_ID = 'PUT_ACCESS_KEY_HERE'
    AWS_SECRET_ACCESS_KEY = 'PUT_SECRET_ACCESS_KEY_HERE'

#### Local Storage
Instead of using a remote cloud location, caretaker will allow you to store your backups locally. Obviously, it is important that you mirror these backups to other off-site locations.

To configure the local storage backend, adjust your settings.py file to contain (for example):

    CARETAKER_BACKUP_BUCKET = 'caretakertestbackup'  # put the name of the backup instance here
    CARETAKER_ADDITIONAL_BACKUP_PATHS = ['/home/user/path1', '/home/user/path2']  # put additional paths to backup here
    CARETAKER_BACKEND = 'Local' # note that this is case sensitive
    CARETAKER_FRONTEND = 'Django'  # note that this is case sensitive
    MEDIA_ROOT = '/var/www/media'  # add your MEDIA ROOT to backup
    CARETAKER_LOCAL_STORE_DIRECTORY = '/path/to/where/you/store/backups'  # specify where to store the backups
    CARETAKER_LOCAL_FILE_PATTERN = '{{version}}.{{date}}'  # this is the recommended format of backup files

There is no Terraform configuration for the local backend.

### Install the Backup Script in Cron
To install a cron line that will run the backup daily at 15 minutes past midnight on the server, run:

    ./manage.py install_cron --action=test
    ./manage.py install_cron

## Usage
Caretaker provides a number of management commands that can be accessed from manage.py:

### Run Backup
This is the most important command. It backs up your database and your media files to the remote store.

    Usage: manage.py run_backup [OPTIONS]

      Pushes LOCAL-FILE to the latest version of REMOTE-KEY

    Options:
      --version                      Show the version and exit.
      -h, --help                     Show this message and exit.
      -v, --verbosity INTEGER RANGE  Verbosity level; 0=minimal output, 1=normal
                                     output, 2=verbose output, 3=very verbose
                                     output.  [0<=x<=3]
      --settings SETTINGS            The Python path to a settings module, e.g.
                                     "myproject.settings.main". If this is not
                                     provided, the DJANGO_SETTINGS_MODULE
                                     environment variable will be used.
      --pythonpath PYTHONPATH        A directory to add to the Python path, e.g.
                                     "/home/djangoprojects/myproject".
      --traceback / --no-traceback   Raise on CommandError exceptions.
      --color / --no-color           Enable or disable output colorization.
                                     Default is to autodetect the best behavior.
      -a, --additional-files TEXT    Additional directories to add to the zip file
      -b, --backend-name TEXT        The name of the backend to use
      -f, --frontend-name TEXT       The name of the frontend to use
      -s, --sql-mode                 Whether to output SQL instead of standard
                                     JSON
      -d, --database TEXT            The database to use
      -a, --alternative-binary TEXT  The alternative binary to use
      --alternative-arguments TEXT   The alternative arguments to use
      --data-file TEXT               The data filename to use
      --archive-file TEXT            The archive filename to use


Example usage:

    manage.py run_backup --output-directory=~/backup -a /home/user/dir1 -a /home/user/dir2

### Push Backup
This command pushes a backup to the server.

    Usage: manage.py push_backup [OPTIONS] REMOTE_KEY LOCAL_FILE

      Pushes LOCAL-FILE to the latest version of REMOTE-KEY

    Options:
      --version                      Show the version and exit.
      -h, --help                     Show this message and exit.
      -v, --verbosity INTEGER RANGE  Verbosity level; 0=minimal output, 1=normal
                                     output, 2=verbose output, 3=very verbose
                                     output.  [0<=x<=3]
      --settings SETTINGS            The Python path to a settings module, e.g.
                                     "myproject.settings.main". If this is not
                                     provided, the DJANGO_SETTINGS_MODULE
                                     environment variable will be used.
      --pythonpath PYTHONPATH        A directory to add to the Python path, e.g.
                                     "/home/djangoprojects/myproject".
      --traceback / --no-traceback   Raise on CommandError exceptions.
      --color / --no-color           Enable or disable output colorization.
                                     Default is to autodetect the best behavior.
      -b, --backend-name TEXT        The name of the backend to use
      -f, --frontend-name TEXT       The name of the frontend to use


Example usage:

    manage.py push_backup --backup-local-file=/home/obc/backups/data.json --remote-key=data.json

### Pull Backup
This command retrieves a backup file from the server. You must also specify the version you wish to retrieve.

    Usage: manage.py pull_backup [OPTIONS] REMOTE_KEY LOCAL_FILE BACKUP_VERSION

      Saves BACKUP-VERSION of REMOTE-KEY into LOCAL-FILE

    Options:
      --version                      Show the version and exit.
      -h, --help                     Show this message and exit.
      -v, --verbosity INTEGER RANGE  Verbosity level; 0=minimal output, 1=normal
                                     output, 2=verbose output, 3=very verbose
                                     output.  [0<=x<=3]
      --settings SETTINGS            The Python path to a settings module, e.g.
                                     "myproject.settings.main". If this is not
                                     provided, the DJANGO_SETTINGS_MODULE
                                     environment variable will be used.
      --pythonpath PYTHONPATH        A directory to add to the Python path, e.g.
                                     "/home/djangoprojects/myproject".
      --traceback / --no-traceback   Raise on CommandError exceptions.
      --color / --no-color           Enable or disable output colorization.
                                     Default is to autodetect the best behavior.
      -b, --backend-name TEXT        The name of the backend to use
      -f, --frontend-name TEXT       The name of the frontend to use


Example:

    manage.py pull_backup --remote-key=data.json --backup-version=jB1dtbf1qraDQhBlKGGDXKAZugEnT2KB --out-file=/home/user/data.json


## Restoring a Backup
Restoring a backup consists of the following steps. First, find the backups that you want:

    manage.py list_backups --remote-key=data.json
    manage.py list_backups --remote-key=backup.tar.gz

You can use grep to find a specific date.

Then pull the files down:

    manage.py pull_backup --remote-key=data.json --backup-version=<INSERT_BACKUP_VERSION_ID> --out-file=/home/user/data.json
    manage.py pull_backup --remote-key=backup.tar.gz --backup-version=<INSERT_BACKUP_VERSION_ID> --out-file=/home/user/backup.tar.gz

Unzip backup.zip and replace the media folders with the results.

Reload the database:

    manage.py loaddata /home/user/data.json

You can also reload the database and media files using the built-in command:

    manage.py import_backup data.json|data.sql|media.zip

## Oracle support
SQL export is not available for Oracle. It's a nightmare to get Oracle tools installed on our testing systems. Hence, Oracle systems will have to use the old dumpdata methods.

## SQLite support
We do not support in-memory SQLite databases for import_file operations. It's not possible to destroy and reload the in-memory database through Django, which is what we do with the on-disk equivalent.

## Post-Execution Hooks
Frontends support post-execution hooks. You can use these to execute commands on the local system after a backup has been created.

To use post-execution hooks, add items to the CARETAKER_POST_EXECUTE variable:

    CARETAKER_POST_EXECUTE = ['rsync -avz --delete {{ local_store_directory }}/{{ backup_bucket }} remote:~/backups',
                          'ls {{ local_store_directory }}/{{ backup_bucket }}']

In post-execution hooks you can get access to CARETAKER_ variables by using the ""{{ variable_name }}"" syntax shown above. Hence, "{{ local_store_directory}}" in a hook will be converted to the value of CARETAKER.LOCAL_STORE_DIRECTORY. Do not include the word "CTVARIABLE" in a post-execute hook.

## Credits
* [A context manager for files or stdout](https://stackoverflow.com/a/17603000/349003) by Wolph.
* [AWS CLI](https://aws.amazon.com/cli/) for interactions with AWS.
* [Captured output](https://stackoverflow.com/a/17981937/349003) by Rob Kennedy.
* [Django](https://www.djangoproject.com/) for the ORM and caching system.
* [django-click](https://github.com/GaretJax/django-click) for command-line management commands.
* [django-dbbackup](https://github.com/jazzband/django-dbbackup) for hints and tips.
* [Git](https://git-scm.com/) from Linus Torvalds _et al_.
* [.gitignore](https://github.com/github/gitignore) from Github.
* [How to read large Popen calls using select](https://stackoverflow.com/a/40929169/349003) by vz0.
* [Rich](https://github.com/Textualize/rich) for beautiful output.
* [Terraform](https://www.terraform.io/) by Hashicorp.

## Test Coverage
![Code Coverage](https://img.shields.io/badge/Code%20Coverage-100%25-success?style=flat)

Package | Line Rate | Branch Rate | Health
-------- | --------- | ----------- | ------
. | 100% | 100% | ✔
caretaker | 100% | 100% | ✔
caretaker.backend | 100% | 100% | ✔
caretaker.backend.backends | 100% | 100% | ✔
caretaker.backend.backends.terraform_aws | 100% | 100% | ✔
caretaker.frontend | 100% | 100% | ✔
caretaker.frontend.frontends | 100% | 100% | ✔
caretaker.frontend.frontends.database_exporters | 100% | 100% | ✔
caretaker.frontend.frontends.database_exporters.django | 100% | 100% | ✔
caretaker.frontend.frontends.database_importers | 100% | 100% | ✔
caretaker.frontend.frontends.database_importers.django | 100% | 100% | ✔
caretaker.management | 100% | 100% | ✔
caretaker.management.commands | 100% | 100% | ✔
caretaker.tests | 100% | 100% | ✔
caretaker.tests.commands | 100% | 100% | ✔
caretaker.tests.frontend | 100% | 100% | ✔
caretaker.tests.frontend.django | 100% | 100% | ✔
caretaker.tests.frontend.django.backend | 100% | 100% | ✔
caretaker.tests.frontend.django.backend.local | 100% | 100% | ✔
caretaker.tests.frontend.django.backend.s3 | 100% | 100% | ✔
caretaker.tests.frontend.django.database_exporters | 100% | 100% | ✔
caretaker.tests.frontend.django.database_importers | 100% | 100% | ✔
caretaker.utils | 100% | 100% | ✔
**Summary** | **100%** (2928 / 2928) | **100%** (675 / 675) | ✔

_Minimum allowed line rate is `60%`_
