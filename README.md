# django-caretaker
django-caretaker ('The Caretaker') is a Django app that backs up your database and media files to a versioned remote object store, such as an AWS S3 bucket. It comes with the Terraform files to provision the required cloud infrastructures (e.g. S3 bucket) and provides management commands to schedule regular backups.

![license](https://img.shields.io/github/license/martinpauleve/django-caretaker) ![activity](https://img.shields.io/github/last-commit/MartinPaulEve/django-caretaker) 

![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white)

[![asciicast](https://asciinema.org/a/HnqOncypouhiHcs4r2mZn0TRS.svg)](https://asciinema.org/a/HnqOncypouhiHcs4r2mZn0TRS)

## Install
To install the module, use pip:

    pip install django-caretaker

Add 'caretaker' to your installed apps in your Django settings file.

Add 'path('caretaker/', include('caretaker.urls')),' to your urls.py file to enable the /caretaker/list view.

django-caretaker requires Python 3.10+ as it makes use of newer language features.

## Setup and Configuration
### Configure a backend and access rights
django-caretaker has the ability to support multiple cloud-based object store backends. However, at the moment, the only backend provider that we have is for Amazon S3. This will expand as the project grows.

#### Amazon S3 / IAM
Ensure that you have a working AWS cli client and configure it if not.

Set the BACKUP_BUCKET variable in your settings.py file. This must be a globally unique name for the S3 bucket. You should also set the MEDIA_ROOT folder so that we know what to back up:

    CARETAKER_BACKUP_BUCKET = 'caretakertestbackup'
    CARETAKER_ADDITIONAL_BACKUP_PATHS = ['/home/user/path1', '/home/user/path2']
    CARETAKER_BACKEND = 'Amazon S3'
    CARETAKER_BACKENDS = ['caretaker.backend.backends.s3']
    MEDIA_ROOT = '/var/www/media'

The CARETAKER_BACKENDS list allows you to specify the available backends. The CARETAKER_BACKEND variable selects the backend to use (there is only S3 at the moment).

Generate and run Terraform configuration in your home directory:

    ./manage.py get_terraform --output-directory=~/terraform_configuration
    cd ~/terraform_configuration
    terraform init
    terraform apply
    terraform output --json

Note down the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and put them in your settings.py file:

    AWS_ACCESS_KEY_ID = 'PUT_ACCESS_KEY_HERE'
    AWS_SECRET_ACCESS_KEY = 'PUT_SECRET_ACCESS_KEY_HERE'

### Install the Backup Script in Cron
To install a cron line that will run the backup daily at 15 minutes past midnight on the server, run:

    ./manage.py install_cron --action=test
    ./manage.py install_cron

## Usage
Caretaker provides a number of management commands that can be accessed from manage.py:

### Run Backup
This is the most important command. It backs up your database and your media files to the remote store.

    usage: manage.py run_backup [-h] [--output-directory OUTPUT_DIRECTORY] [-a ADDITIONAL_FILES] [--version] [-v {0,1,2,3}] [--settings SETTINGS]
                            [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color] [--skip-checks]
    
    Creates a backup set and pushes it to the remote store

Example usage:

    manage.py run_backup --output-directory=~/backup -a /home/user/dir1 -a /home/user/dir2

### Push Backup
This command pushes a backup to the server.

    usage: manage.py push_backup [-h] [--backup-local-file BACKUP_LOCAL_FILE] [--remote-key REMOTE_KEY] [--version] [-v {0,1,2,3}]
                             [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color] [--skip-checks]
    
    Pushes the backup SQL to the remote store

Example usage:

    manage.py push_backup --backup-local-file=/home/obc/backups/data.json --remote-key=data.json

### Pull Backup
This command retrieves a backup file from the server. You must also specify the version you wish to retrieve.

    usage: manage.py pull_backup [-h] [--backup-version BACKUP_VERSION] [--out-file OUT_FILE] [--remote-key REMOTE_KEY] [--version]
                             [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color]
                             [--skip-checks]
    
    Pulls a specific backup SQL from the remote store

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

## Credits
* [AWS CLI](https://aws.amazon.com/cli/) for interactions with AWS.
* [Django](https://www.djangoproject.com/) for the ORM and caching system.
* [django-dbbackup](https://github.com/jazzband/django-dbbackup) for hints and tips.
* [Git](https://git-scm.com/) from Linus Torvalds _et al_.
* [.gitignore](https://github.com/github/gitignore) from Github.
* [Rich](https://github.com/Textualize/rich) for beautiful output.
* [Terraform](https://www.terraform.io/) by Hashicorp.