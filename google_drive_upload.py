"""Gather, analyze and upload image files to Google Drive."""
import os
import mimetypes
import httplib2
from apiclient import discovery
from quickstart import get_credentials


IMAGE_EXTS = set()
OTHER_EXTS = set()
for ext, mimetype in mimetypes.types_map.items():
    if mimetype.startswith('image'):
        IMAGE_EXTS.add(ext)
    else:
        OTHER_EXTS.add(ext)


def iter_directory(path):
    """Generate the files from a given directory path."""
    if not os.path.isdir(path):
        raise ValueError('No such directory: {}'.format(path))
    for filename in os.listdir(path):
        yield filename


def is_image_filename(filename):
    """Check if a given filename is an image type."""
    ext = filename[filename.rfind('.'):]
    return ext in IMAGE_EXTS


def make_google_drive_service():
    """Create a new instance of a Google Drive API service."""
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    return discovery.build('drive', 'v3', http=http)
