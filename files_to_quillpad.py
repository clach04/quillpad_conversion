#!/usr/bin/env python
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
"""Generate QuillPad https://github.com/quillpad/quillpad json file for import from *.md and *.txt files

NOTE only does current directory, not nested/sub-directories
Does not handle git checkouts/repos (with deleted files)

Schemas seen in the wild:

    {
        "version": "13",
        "notes": [
            {
                "id": 1,
                "title": "Title separate from body",
                "modifiedDate": 1691889723,
                "creationDate": 1691889723,
                "content": "Body content here.\n\nFormat SQLite3... In a zip when exported.\n\n# h1\n\n## h2\n\nAnd bullet points:\n\n  * Here\n\nDoes not autobullet :-(\n\nNumbered:\n\n  1. One\n  2. Manual\n\n\n\nLabels are tags?",
                "isMarkdownEnabled": false
            }
        ],
        "tags": [],
        "joins": []
    }


    {
        "version": 17,
        "notes": [
            {
                "id": 1,
                "title": "Test not title",
                "modifiedDate": 1691912414,
                "creationDate": 1691756901,
                "content": "Test note body.\n\nJson in a zip, similar but not the same as gitjournal.\n\n# h1\n\n## h2\n\nBullet points.\n\nBullets:\n* Points\n* auto bullet! Love it :-)\n\nNumbered bullets?\n1. One\n2. Two, yep autos these too.\n\n\nDefaults to view mode which I like but am not yet used to.",
                "isMarkdownEnabled": false
            }
        ]
    }



"modifiedDate": 1691912414 == datetime.datetime.fromtimestamp(1691912414) == datetime.datetime(2023, 8, 13, 0, 40, 14) -- LOCAL TIME
"creationDate": 1691756901 == datetime.datetime.fromtimestamp(1691756901) == datetime.datetime(2023, 8, 11, 5, 28, 21)

"""

import zipfile
from io import BytesIO as FakeFile  # py3
import datetime
import glob
import fnmatch
import json
import os
import string
import sys
import time
import uuid
import zipfile


is_py3 = sys.version_info >= (3,)
is_win = sys.platform.startswith('win')
extensions_to_check = ['.md', '.txt']  # NOTE case sensitive  # TODO consider using fnmatch and case insensitive

class InMemoryZip(object):
    def __init__(self):
        # Create the in-memory file-like object
        self.in_memory_zip = FakeFile()

    def append(self, filename_in_zip, file_contents):
        '''Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip.'''
        # Get a handle to the in-memory zip in append mode
        zf = zipfile.ZipFile(self.in_memory_zip, "a", zipfile.ZIP_DEFLATED, False)

        # Write the file to the in-memory zip
        zf.writestr(filename_in_zip, file_contents)

        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zfile in zf.filelist:
            zfile.create_system = 0

        return self
      
    def contents(self):
        '''Returns a string with the contents of the in-memory zip.'''
        return self.in_memory_zip.getvalue()

    def write_to_file(self, filename):
        '''Writes the in-memory zip to a file.'''
        f = open(filename, "wb")
        f.write(self.contents())
        f.close()


def pattern_to_file_list(pattern):
    filenames = []
    for filename_pattern in extensions_to_check:
        filenames += glob.glob(pattern + filename_pattern)
    return filenames


def filename_to_entry(filename, note_id):
    ctime = os.path.getctime(filename)
    mtime = os.path.getmtime(filename)
    # string in ISO format without micro/milli-secs and Z
    #time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime('.bashrc')))  # local time
    #time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(os.path.getmtime('.bashrc')))  # UTC / GMT
    #
    # datetime
    #datetime.datetime.fromtimestamp(os.path.getmtime('.bashrc'))  # local

    f = open(filename, 'rb')
    binary_data = f.read()
    f.close()
    note_content = binary_data.decode('utf-8')  # TODO other encoding options
    # TODO newline translation is needed here. expected to be Unix new lines "\n".
    note_content = note_content.replace("\r\n", "\n")
    try:
        title, content = note_content.split('\n', 1)
    except ValueError:
        title = note_content
        content = ""
    title = title.strip()
    content = content.lstrip()  # remove **leading** blank lines from content  (also indents which may not want but this isn't bad for first POC

    result = {
        "id": note_id,
        "title": title,
        "modifiedDate": int(mtime),
        "creationDate": int(ctime),
        "content": content,
        "isMarkdownEnabled": False,
    }
    return result


filenames = pattern_to_file_list('*')

now = datetime.datetime.now()
print('%d files to export' % len(filenames))
output_filename = os.environ.get('QUILLPAD_EXPORT_FILENAME', 'quillpad_%s.zip' % now.strftime('%Y%m%d_%H%M%S'))
print('to export %r' % output_filename)
notes = []
for note_id, filename in enumerate(filenames, 1):
    print('%s' % filename)
    notes.append(filename_to_entry(filename, note_id))
    #break  # debug, just the one file for experiments

simplenotes_dict = {
    "version": "13",
    "notes": notes,
    "tags": [],
    "joins": [],
}

json_str = json.dumps(simplenotes_dict, indent=4)
#print('%s' % json_str)
"""
output_filename = os.environ.get('QUILLPAD_EXPORT_FILENAME', 'backup.json')  # TODO wrap in a zip file
f = open(output_filename, 'wb')
f.write(json_str.encode('utf-8'))
f.close()
"""
imz = InMemoryZip()
imz.append("backup.json", json_str.encode('utf-8'))
imz.write_to_file(output_filename)
#print(repr(imz.contents()))

