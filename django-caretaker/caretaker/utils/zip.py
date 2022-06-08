from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from caretaker.utils import file as file_util


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
                zf.write(file, file.relative_to(directory.parent))

    return Path(output_file)
