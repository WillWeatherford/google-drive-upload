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


def get_file_data(filename):
    """Return number of bytes aka content length and content type."""
    return 0, 'image/jpeg'


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


def start_upload(filename, content_type, byte_size):
    """Start a resumable file upload and return the resumeable upload id."""
    credentials = get_credentials()
    headers = {
        'Authorization': 'Bearer {}'.format(credentials.access_token),
        'Content-Length': '38',  # needs to be variable too
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Upload-Content-Type': content_type,
        'X-Upload-Content-Length': byte_size,
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


def save_local_file_data(filename, **kwargs):
    """Save the data for the uploading file in a local json file."""
    with open(JSON_DATA_FILE, 'r+') as json_file:
        data = json.load(json_file)
        data[filename].update(kwargs)
        json.dump(data, json_file)


def get_local_file_data(filename):
    """Get file information from local json file."""
    with open(JSON_DATA_FILE, 'r') as json_file:
        data = json.load(json_file)
        try:
            return data['filename']
        except KeyError:
            raise ValueError('File is not in local data: {}'.format(filename))


def begin_file_upload(filename, resume_uri, content_type, byte_size):
    """Make PUT request with content size and resumable URI."""
    headers = {
        'Content-Length': byte_size,
        'Content-Type': content_type,
    }
    file_bytes = open(filename, 'rb')
    requests.put(resume_uri, headers=headers, files={filename: file_bytes})


def get_upload_completion_status(resume_uri, byte_size):
    """Request the amount of bytes already completed in the upload."""
    headers = {
        'Content-Length': 0,
        'Content-Range': 'bytes */{}'.format(byte_size),
    }
    response = requests.put(resume_uri, headers=headers)
    return int(response.headers['Range'].split('-')[1])


def resume_file_upload(filename, progress, byte_size):
    """Resume a file upload with information on its completion status."""
    start = progress + 1
    headers = {
        'Content-Length': byte_size - start,
        'Content-Range': 'bytes {}/{}'.format(progress, byte_size),
    }
    requests.put(resume_uri, headers=headers)


def insert_placeholder(filename, service):
    """Insert 0 byte file onto Google Drive instead of real thing."""


def process_computer_vision(filename):
    """Dummy function simulating real processing of file by computer vision."""
    return random.choice([0, 1])


def main():
    """Main process loop."""
    service = make_google_drive_service()
    image_files = filter(is_image_filename, iter_directory)

    for filename in image_files:
        byte_size, content_type = get_file_data(filename)
        try:
            file_data = get_local_file_data(filename)
        except ValueError:
            file_data = {}
            cv_result = process_computer_vision(filename)
            if not cv_result:
                insert_placeholder(filename, service)
                save_local_file_data(filename, complete=True)
                continue

        if file_data.get('is_complete'):
            # Better to save locally than to always query API for completeness
            continue

        try:
            resume_uri = file_data['resume_uri']
            progress = get_upload_completion_status(resume_uri, byte_size)
        except KeyError:
            # no record in google of this upload ever having started
            resume_uri = begin_file_upload(filename, content_type, byte_size)
            save_local_file_data(filename, resume_uri=resume_uri, complete=False)
            progress = 0

        resume_file_upload(filename, progress, byte_size)


if __name__ == '__main__':
    main()
