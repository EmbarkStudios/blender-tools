''' Functions for handling paths in the current project. '''
from os import path, listdir
import json
import bpy
from . import get_preferences
from .functions import message_box


def get_source_path():
    """Returns the Embark Addon's Project source folder."""
    prefs = get_preferences()
    if prefs.proj_path_file:
        return path.dirname(prefs.proj_path_file)
    return None


def get_path_lookup_table():
    ''' Gets the path lookup dictionary from addon prefs '''
    lookup_table = {}
    prefs = get_preferences()
    if path.exists(prefs.proj_path_file):
        with open(prefs.proj_path_file, 'r') as read_file:
            for key, value in json.load(read_file).items():
                lookup_table.update({key: value})
        return lookup_table
    return None


def is_source_path_valid(show_warning=False):
    ''' Checks whether Project source folder is valid '''
    prefs = get_preferences()
    if prefs.proj_path_file:
        return True
    if show_warning:
        message = "Source path is not valid! Please check your source path in the Embark Addon preferences."
        bpy.ops.wm.open_addon_prefs('INVOKE_DEFAULT', message=message)
    return False


def make_project_path_absolute(file_path):
    """
    Returns an absolute path by joining the project RAW dir with a given file_path.
    Assumes that the file_path is local. Does not validate that the result actually exists.

    :param file_path: local file path below proj_raw
    :type file_path: string
    :return: absolute file path
    :rtype: string
    """
    proj_raw = get_source_path()
    if proj_raw and path.isdir(proj_raw):
        if not path.isabs(file_path):
            return path.normpath(path.join(path.abspath(proj_raw), file_path))
    return None


def get_key_path_absolute(key):
    """
    Gets the path absolute path of the supplied path key
    :param key: A path-key, such as Animation, Rig,
    :return:
    """
    if is_source_path_valid():
        proj_path_lookup = get_path_lookup_table()
        if proj_path_lookup:
            project_path = proj_path_lookup.get(key, False)
            if project_path is False:
                message_box(
                    message=f'"{key}" could not be found in {make_project_path_absolute("Project.paths")}',
                    title='KeyError',
                    icon='ERROR'
                )
                return None
            return make_project_path_absolute(project_path)
    return None


def get_path_relative_to_key(key, file_path):
    """
    Returns a path expressed as relative to the supplied project key
    :param key:
    :type key: string
    :param file_path:
    :type file_path: string
    :return: Path relative to the key in the project
    :rtype: string
    """
    project_path = get_key_path_absolute(key)
    nrm_path = path.normpath(file_path)

    if project_path in nrm_path:
        return nrm_path.replace(project_path, '').lstrip("\\")

    return file_path


def validate_path(file_path):
    """
    Checks if file_path is valid compared to the Project source folder
    :param file_path: The path to check
    :type file_path: string
    :return: Path relative to the Project source folder if valid, otherwise None
    :rtype: string or NoneType
    """
    if not file_path:
        return None

    source_path = get_source_path()
    if not source_path:
        print("Warning: Source path was not defined!")
        return None

    source_path = path.normpath(source_path)

    if not path.isabs(file_path):
        file_path = path.normpath(path.join(source_path, file_path))

    file_path = path.normpath(file_path)
    if file_path.lower().startswith(source_path.lower()):
        return "./" + path.relpath(file_path, source_path)

    print(f"Warning: Path must be relative to: {source_path}")
    return None


def validate_file(filepath, ext=None):
    """ Verifies that a file exists, and if it is of a certain type """
    validated_relative_path = validate_path(filepath)
    if not validated_relative_path:
        return False
    filepath = make_project_path_absolute(validated_relative_path)
    if path.isfile(filepath) and not ext:
        return True
    elif path.isfile(filepath) and path.splitext(filepath)[-1] == ext:
        return True
    return False


def get_all_filepaths_in_dir(dirpath):
    ''' Returns all file paths in a directory. '''
    if path.isdir(dirpath):
        filepaths = [path.join(dirpath, f) for f in listdir(dirpath) if path.isfile(path.join(dirpath, f))]
        return filepaths
    return None


def get_all_filenames_in_dir(dirpath):
    ''' Returns all file names in a directory. '''
    if path.isdir(dirpath):
        file_names = [path.splitext(f)[0] for f in listdir(dirpath) if path.isfile(path.join(dirpath, f))]
        return file_names
    return None
