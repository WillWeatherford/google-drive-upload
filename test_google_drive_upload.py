"""Tests for Google Drive Image Upload program."""
from __future__ import print_function, unicode_literals
import random
import pytest
import string
from itertools import product
from apiclient.discovery import Resource
from google_drive_upload import IMAGE_EXTS, OTHER_EXTS

FAKE_BINARY = b'10101010101010101010101010101010101010110101010101010'
DIR_CONTENTS = product((0, random.randrange(1000)), (random.randrange(1000), 0))


def _make_filename(is_image, ext=None):
    """Make a filename, either an image or some other extension."""
    if ext is None:
        ext = random.choice(list(IMAGE_EXTS) if is_image else list(OTHER_EXTS))
    filename = ''.join(random.sample(string.ascii_letters, 10))
    return ''.join((filename, ext))


@pytest.fixture(params=DIR_CONTENTS)
def temp_image_directory(request, tmpdir):
    """Generate a temporary directory fixture.

    Populated with 0-999 image files and 0-999 non-image files.
    """
    num_images, num_other = request.param
    image_dir = tmpdir.mkdir('images')
    for _ in range(num_images):
        image_dir.join(_make_filename(True)).write_binary(FAKE_BINARY)
    for _ in range(num_other):
        image_dir.join(_make_filename(False)).write_binary(FAKE_BINARY)
    return image_dir, num_images, num_other


@pytest.fixture(params=IMAGE_EXTS)
def image_filename(request, tmpdir):
    """Generate valid image files in temporary directory."""
    ext = request.param
    file = tmpdir.join(_make_filename(True, ext))
    file.write_binary(FAKE_BINARY)
    return file.strpath


@pytest.fixture(params=OTHER_EXTS)
def other_filename(request, tmpdir):
    """Generate invalid non-image files in temporary directory."""
    ext = request.param
    file = tmpdir.join(_make_filename(False, ext))
    file.write_binary(FAKE_BINARY)
    return file.strpath


def test_base_true():
    """Base level test."""
    assert True


########################################################################
# Tests for iterating over local directory and finding image files

def test_iter_directory_arg():
    """Test that iter_directory requires an argument."""
    from google_drive_upload import iter_directory
    with pytest.raises(TypeError):
        iter_directory()


def test_iter_directory_invalid():
    """Test that iter_directory raises ValueError when given an invalid dir."""
    from google_drive_upload import iter_directory
    with pytest.raises(ValueError):
        list(iter_directory('not/a/real/dir'))


def test_iter_directory_size(temp_image_directory):
    """Test that iter_directory generates expected number of files."""
    from google_drive_upload import iter_directory
    image_dir, num_images, num_other = temp_image_directory
    results = iter_directory(image_dir.strpath)
    assert len(list(results)) == num_images + num_other


def test_is_image_true(image_filename):
    """Test that is_image returns true when expected."""
    from google_drive_upload import is_image_filename
    assert is_image_filename(image_filename)


def test_is_image_false(other_filename):
    """Test that is_image returns true when expected."""
    from google_drive_upload import is_image_filename
    assert not is_image_filename(other_filename)


def test_filter_images_size(temp_image_directory):
    """Test that is_image_filename yields expected amount as filter."""
    from google_drive_upload import iter_directory, is_image_filename
    image_dir, num_images, num_other = temp_image_directory
    result = filter(is_image_filename, iter_directory(image_dir.strpath))
    assert len(list(result)) == num_images


########################################################################
# Tests for connecting to Google Drive API

def test_credentials_valid():
    """Test that get_credentials from quickstart still works."""
    from quickstart import get_credentials
    credentials = get_credentials()
    assert not credentials.invalid


def test_make_google_drive_service():
    """Test that a google drive service instance is created smoothly."""
    from google_drive_upload import make_google_drive_service
    service = make_google_drive_service()
    assert isinstance(service, Resource)
