"""Tests for Google Drive Image Upload program."""
from __future__ import print_function, unicode_literals
import random
import pytest
import string
import mimetypes
from itertools import product

IMAGE_EXTS = []
OTHER_EXTS = []
for ext, mimetype in mimetypes.types_map.items():
    if mimetype.startswith('image'):
        IMAGE_EXTS.append(ext)
    else:
        OTHER_EXTS.append(ext)

DIR_CONTENTS = product((0, random.randrange(1000)), (random.randrange(1000), 0))


def _make_filename(is_image):
    """Make a filename, either an image or some other extension."""
    ext_list = IMAGE_EXTS if is_image else OTHER_EXTS
    ext = random.choice(ext_list)
    filename = random.sample(string.ascii_letters, random.randrange(3, 20))
    return '.'.join((filename, ext))


@pytest.fixture(params=DIR_CONTENTS)
def temp_image_directory(request, tmpdir):
    """Generate a temporary directory fixture.

    Populated with 0-999 image files and 0-999 non-image files.
    """
    num_images, num_other = request.param
    image_dir = tmpdir.mkdir('images')
    for _ in range(num_images):
        image_dir.join(_make_filename(True))
    for _ in range(num_other):
        image_dir.join(_make_filename(False))
    return image_dir


def test_base_true():
    """Base level test."""
    assert True


def test_iter_directory_arg():
    """Test that iter_directory requires an argument."""


def test_iter_directory_invalid():
    """Test that iter_directory raises ValueError when given an invalid dir."""


def test_iter_directory_size(temp_image_directory):
    """Test that iter_directory generates expected number of files."""
