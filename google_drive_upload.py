"""Gather, analyze and upload image files to Google Drive."""
import os
import sys
import json
import time
import random
import httplib2
import requests
import mimetypes
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
JSON_DATA_FILE = 'local_data.json'

# These are hard-coded; could be passed in as CLI args or gotten from conf file
NUM_RETRIES = 5
MIN_DELAY = 3
MAX_DELAY = 20


def delay_and_retry(func):
    """Handle delays and retries for functions making requests."""
    def wrapped(*args, **kwargs):
        """Put delays and re-tries to decorated functions."""
        # Initial random delay to ease over-taxing from multiple threads
        time.sleep(random.randrange(MIN_DELAY, MAX_DELAY))

        # Exponential back-off retry
        for n in range(NUM_RETRIES):
            try:
                return func(*args, **kwargs)
            except requests.HTTPError as exception:
                time.sleep(2 ** n)
        raise exception


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


def get_file_byte_size(filename):
    """Return number of bytes aka content length of a given file by name."""
    return '{}'.format(os.path.getsize(filename))


def get_file_mimetype(filename):
    """Return the mimetype of a given file by name."""
    return mimetypes.guess_type(filename)[0]


def get_access_token():
    """Get an access token for Google Drive API."""
    credentials = get_credentials()
    if credentials.access_token_expired:
        credentials.refresh(httplib2.Http())
    return credentials.access_token


def save_local_file_data(filename, **kwargs):
    """Save the data for the uploading file in a local json file."""
    try:
        with open(JSON_DATA_FILE, 'r') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        pass
    with open(JSON_DATA_FILE, 'w') as json_file:
        data.setdefault(filename, {}).update(kwargs)
        json.dump(data, json_file)


def get_local_file_data(filename):
    """Get file information from local json file."""
    try:
        with open(JSON_DATA_FILE, 'r') as json_file:
            data = json.load(json_file)
            try:
                return data['filename']
            except KeyError:
                raise ValueError('File not in local data: {}'.format(filename))
    except FileNotFoundError:
        with open(JSON_DATA_FILE, 'w') as json_file:
            json.dump({}, json_file)
            raise ValueError('File not in local data: {}'.format(filename))


@delay_and_retry
def upload_placeholder(filename, access_token):
    """Insert 0 byte file onto Google Drive instead of real thing."""
    headers = {
        'Host': 'www.googleapis.com',
        'Content-Type': 'image/jpeg',
        'Authorization': 'Bearer {}'.format(access_token),
        'Content-Length': 0,
    }
    params = {'uploadType': 'media'}
    response = requests.post(
        UPLOAD_URL,
        params=params,
        headers=headers,
        files={filename: b''},
    )
    response.raise_for_status()


@delay_and_retry
def start_upload_session(filename, content_type, byte_size, access_token):
    """Start a resumable file upload and return the resumeable upload id."""
    headers = {
        'Authorization': 'Bearer {}'.format(access_token),
        'Content-Length': '38',  # needs to be variable too
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Upload-Content-Type': content_type,
        'X-Upload-Content-Length': byte_size,
    }
    response = requests.post(
        UPLOAD_URL,
        headers=headers,
        json={'name': filename},
        params={'uploadType': 'resumable'},
    )
    response.raise_for_status()
    try:
        return response.headers['Location']
    except KeyError:
        raise ValueError('Failed to get upload ID ')


@delay_and_retry
def begin_file_upload(filename, filepath, resume_uri, content_type, byte_size, access_token):
    """Make PUT request with content size and resumable URI."""
    headers = {
        'Authorization': 'Bearer {}'.format(access_token),
        'Content-Length': byte_size,
        'Content-Type': content_type,
    }
    with open(filepath, 'rb') as file_buffer:
        file_bytes = file_buffer.read()
        response = requests.put(resume_uri, headers=headers, files={filename: file_bytes})
        response.raise_for_status()


@delay_and_retry
def get_upload_progress(resume_uri, byte_size, access_token):
    """Request the amount of bytes already completed in the upload."""
    headers = {
        'Authorization': 'Bearer {}'.format(access_token),
        'Content-Length': '0',
        'Content-Range': 'bytes */{}'.format(byte_size),
    }
    response = requests.put(resume_uri, headers=headers)
    response.raise_for_status()
    return int(response.headers['Range'].split('-')[1])


@delay_and_retry
def resume_file_upload(filename, filepath, resume_uri, progress, byte_size, access_token):
    """Resume a file upload with information on its completion progress."""
    start = progress + 1
    byte_size = int(byte_size)

    headers = {
        'Authorization': 'Bearer {}'.format(access_token),
        'Content-Length': '{}'.format(byte_size - start),
        'Content-Range': 'bytes {}/{}'.format(progress, byte_size),
    }
    with open(filepath, 'rb') as file_buffer:
        file_bytes = file_buffer.read()[start:]
        response = requests.put(resume_uri, headers=headers, files={filename: file_bytes})
        response.raise_for_status()


def process_computer_vision(filepath):
    """Dummy function simulating real processing of file by computer vision."""
    # return random.choice([0, 1])
    return True


def main(directory):
    """Main process loop."""
    access_token = get_access_token()

    for filename in filter(is_image_filename, iter_directory(directory)):

        filepath = os.path.join(directory, filename)
        byte_size = get_file_byte_size(filepath)
        content_type = get_file_mimetype(filepath)

        try:
            file_data = get_local_file_data(filename)
        except ValueError:
            file_data = {}
            cv_result = process_computer_vision(filename)
            if not cv_result:
                upload_placeholder(filename, access_token)
                save_local_file_data(filename, complete=True)
                continue

        if file_data.get('is_complete'):
            # Better to save locally than to always query API for completeness
            continue

        try:
            resume_uri = file_data['resume_uri']
            progress = get_upload_progress(resume_uri, byte_size, access_token)
        except KeyError:
            # no record in google of this upload ever having started
            resume_uri = start_upload_session(filename, content_type, byte_size, access_token)
            save_local_file_data(filename, resume_uri=resume_uri, complete=False)
            progress = 0

        # Either begin or resume upload, depending if any progress has been made
        if progress:
            resume_file_upload(filename, filepath, resume_uri, progress, byte_size, access_token)
        else:
            begin_file_upload(filename, filepath, resume_uri, content_type, byte_size, access_token)

        # If we reach this far, the file upoad is complete.
        save_local_file_data(filename, complete=True)


if __name__ == '__main__':
    try:
        directory = sys.argv[1]
    except IndexError:
        sys.exit()
    else:
        main(directory)
