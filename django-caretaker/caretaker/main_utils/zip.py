from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def create_zip_file(input_paths, output_file):
    with ZipFile(output_file.expanduser(), 'w', ZIP_DEFLATED) as zf:
        for directory in input_paths:
            for file in directory.rglob('*'):
                zf.write(file, file.relative_to(directory.parent))

    return Path(output_file)
