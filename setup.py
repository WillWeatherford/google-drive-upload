"""Setup for Google Drive Image Uploader package."""
from __future__ import print_function, unicode_literals
from setuptools import setup, find_packages


setup(name='Google Drive Image Uploader',
      version='0.0',
      description='Utility to upload local image files to Google Drive.',
      author=('Will Weatherford'),
      author_email='weatherford.william@gmail.com',
      url='',
      license='MIT',
      keywords='google drive api',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='google-drive-upload',
      entry_points="""\
      [console_scripts]
      google-drive=google_drive_upload:main
      """,
      )
