from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from caretaker.utils import file as file_util
from caretaker.utils import log


def create_zip_file(input_paths: list, output_file: Path) -> Path:
    """
    Create a zip file that stores all input paths inside

    :param input_paths: a list of input directories
    :param output_file: the output file to write
    :return: a pathlib.Path object pointing to the zip
    """
    with ZipFile(file_util.normalize_path(output_file),
                 'w', ZIP_DEFLATED) as zf:
        for directory in input_paths:
            for file in directory.rglob('*'):
                zf.write(file)

    return Path(output_file)


def unzip_file(input_file: Path, dry_run: bool) -> None:
    """
    Unzip a zip file

    :param input_file: a zip file to unzip
    :param dry_run: whether to operate in dry run mode
    :return: a pathlib.Path object pointing to the zip
    """
    with ZipFile(input_file, 'r') as zf:
        if not dry_run:
            zf.extractall('/')
        else:
            logger = log.get_logger('zip-extractor')
            logger.info('Operating in dry run mode. No changes will be made.')

            file_list = zf.namelist()

            for file_name in file_list:
                logger.info('Would extract /{}'.format(file_name))
