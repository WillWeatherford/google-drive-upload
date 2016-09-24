"""Gather, analyze and upload image files to Google Drive."""
import os
import json
import httplib2
import requests
import mimetypes
import random
from apiclient import discovery
from quickstart import get_credentials

IDS_COUNT = 20
IMAGE_EXTS = set()
OTHER_EXTS = set()
for ext, mimetype in mimetypes.types_map.items():
    if mimetype.startswith('image'):
        IMAGE_EXTS.add(ext)
    else:
        OTHER_EXTS.add(ext)
UPLOAD_URL = 'https://www.googleapis.com/upload/drive/v3/files'
JSON_DATA_FILE = 'local_storage.json'


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


def get_google_file_ids(service):
    """Get a new batch of file ids for Google Drive with given service."""
    files_resrc = service.files()
    get_ids_request = files_resrc.generateIds(space='drive', count=IDS_COUNT)
    response = get_ids_request.execute()
    return set(response['ids'])


def start_upload(filename, u_content_type, u_content_length):
    """Start a resumable file upload and return the resumeable upload id."""
    credentials = get_credentials()
    headers = {
        'Authorization': 'Bearer {}'.format(credentials.access_token),
        'Content-Length': '38',  # needs to be variable too
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Upload-Content-Type': u_content_type,
        'X-Upload-Content-Length': u_content_length,
    }
    params = {'uploadType': 'resumable'}
    json = {'name': filename}
    response = requests.post(
        UPLOAD_URL,
        params=params,
        headers=headers,
        json=json,
    )
    try:
        return response.headers['Location']
    except KeyError:
        raise ValueError('Failed to get upload ID ')


def save_file_upload_data(filename, file_id, upload_id):
    """Save the data for the uploading file in a local json file."""
    with open(JSON_DATA_FILE, 'r+') as json_file:
        data = json.load(json_file)
        data[filename] = {'file_id': file_id, 'upload_id': upload_id}
        json.dump(data, json_file)


def get_file_upload_data(filename):
    """Get file information from local json file."""
    with open(JSON_DATA_FILE, 'r') as json_file:
        data = json.load(json_file)
        return data.get('filename', {})


def begin_file_upload(filename, u_content_type, u_content_length):
    """Make PUT request with content size and resumable URI."""


def get_upload_completion_status(resumable_uri, u_content_length):
    """Request the amount of bytes already completed in the upload."""


def resume_file_upload(filename, progress, u_content_length):
    """Resume a file upload with information on its completion status."""


def insert_placeholder(filename, service):
    """Insert 0 byte file onto Google Drive instead of real thing."""


def process_computer_vision(filename):
    """Dummy function simulating real processing of file by computer vision."""
    return random.choice([0, 1])
