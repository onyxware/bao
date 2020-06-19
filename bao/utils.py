# coding: utf8
"""Helper functions, utilites, etc."""

import ast
import os
import shutil
import sys
import pathlib
import re
import zipfile

from .exceptions import BaoError

PACKAGE_ATTRIBUTES = {
    "name": None,
    "author": None,
    "license": None,
    "copyright": "",
    "version": None,
    "doc": "",
    "maintainer": "",
    "email": "",
    "pip_requires": [],
}

# String parsing from https://stackoverflow.com/a/19675957
RE_META_ATTR = re.compile(r"\_\_([a-z]+)\_\_ *= *['\"](.*?)['\"]")
EMPTY_ZIP_FILE = b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


def _fill_defaults(data: dict, defaults: dict):
    """Fill in default values into a dictionary.
    
    Args:
        data: The dictionary to fill with default values.
        defaults: The default values. If a key in defaults is not found in data, the
        value of the key in defaults will be put into data.
        If the value of the key in defaults is None, a KeyError will be raised.
    """

    for key, value in defaults.items():
        result = data.get(key, None)
        if result is None:
            if value is not None:
                data[key] = value
            else:
                raise KeyError(f"field required: {key}")


def copypath(src: str, dst: str) -> None:
    """Copy a path to a destination.
    
    Args:
        src: The path to copy. Must be an existing file/directory.
        dst: The path to copy to. Must be an directory.
    
    Returns:
        None.
    """

    src = pathlib.Path(src)

    if src.is_file():
        shutil.copy2(src, dir)

    elif src.is_dir():
        folder_dest = pathlib.Path(dst) / src.name
        shutil.copytree(src, folder_dest)

    else:
        raise shutil.Error("src is not a file or dir")


def valid_module_path(pth: pathlib.Path) -> bool:
    """Check if a path to a Python module is valid (either ends with ".py",
    or is a folder with a __init__.py file).
    
    Returns:
        True if the path exists and is a Python module, False if the path does not
        exist/is not a valid Python module.
    """
    
    pth = pathlib.Path(pth)

    return (pth.is_file() and pth.suffix == ".py") or (
        pth.is_dir() and (pth / "__init__.py").is_file()
    )


def autogen_metadata(module_path: str) -> dict:
    """Generate metadata for a bao package from a Python module (.py file).

    Basically, we find all __{ATTR}__ constants that are defined and return them.
    
    Args:
        module_path: The path to the module, must be a standalone Python script.

    Raises:
        SyntaxError, if the module code is invalid.
    
    Returns:
        dict: The metadata generated.
    """

    metadata = {}
    module_path = pathlib.Path(module_path).resolve().expanduser()
    metadata["name"] = module_path.stem

    try:
        with module_path.open("r", encoding="utf-8") as f:
            data = f.read()

    except FileNotFoundError:
        data = ""

    metadata["docstring"] = ast.get_docstring(ast.parse(data))

    attrs = [line for line in data.splitlines() if line.startswith("__")]

    for line in attrs:
        try:
            attr, attr_data = RE_META_ATTR.findall(line)[0]

        except (TypeError, ValueError):
            continue

        else:
            metadata[attr] = attr_data

    return metadata


def zipdir(path: pathlib.Path, zf: zipfile.ZipFile) -> zipfile.ZipFile:
    """Compress a directory's contents into a ZipFile.
    
    Args:
        path: The path to the directory.
        zf: The zipfile object to write to.
    
    Returns:
        The zipfile object that was written to.
    
    Raises:
        NotADirectoryError, if the path is not a directory.
        TypeError, if the zipfile is not a ZipFile object.
    """

    pth = pathlib.Path(path)
    if not path.is_dir():
        raise NotADirectoryError("can't compress path: not a directory")

    if not isinstance(zf, zipfile.ZipFile):
        raise TypeError("not a zipfile")

    for root, dirs, files in os.walk(pth):
        for file in files:
            filepath = pathlib.Path(root) / file
            relpath = pth.name / filepath.relative_to(pth)
            print(relpath)
            zf.write(filepath, arcname=relpath)

    return zf