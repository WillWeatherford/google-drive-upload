"""Gather, analyze and upload image files to Google Drive."""
import os


def iter_directory(path):
    """Generate the files from a given directory path."""
    if not os.path.isdir(path):
        raise ValueError('Given directory path is not a directory.')
    for filename in os.listdir(path):
        yield filename
