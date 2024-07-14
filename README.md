# Quillpad Conversion

Conversion tools for [Quillpad](https://github.com/quillpad/quillpad) (nee [Quillnote](https://github.com/msoultanidis/quillnote)) notes.

Python 3 and 2 scripts for converting to QuillPad.

## Notes

QuillPad schema is not documented, see https://github.com/quillpad/quillpad/discussions/271 for now:

  * Source code of these tools for examples/notes https://github.com/clach04/quillpad_conversion/blob/4697b44f65ccd0294aed92c130e8b063cda2e9c1/files_to_quillpad.py#L10

## Tools

### Plain text files to QuillPad

    python files_to_quillpad.py

Generates export filename based on current time/date. To specify
filename set operating system environment variable
`QUILLPAD_EXPORT_FILENAME` to expected filename (recommend
including .zip extension).

**WARNING** ⚠️ see https://github.com/quillpad/quillpad/issues/270 do not import more than once!

### Notally to QuillPad

[Notally](https://github.com/OmGodse/Notally) conversion to [Quillpad](https://github.com/quillpad/quillpad)

notallyToQuillPad.py modified version of https://gist.github.com/nWestie/224d14a6efd00661b5c93040c7511816

Includes Windows support and correct file name for export (as of 2024).

## Other Tools

  * https://github.com/MolassesLover/jotbook - reverse of files_to_quillpad.py
  * https://github.com/arunk140/quillnote-server sync server (uses a sqlite3 database)
  * https://github.com/Eve1374/GKeepToQuillpad Google Keep converter
  * https://github.com/phazejeff/colornote-to-quillpad
  * https://github.com/clach04/pysimplenote related

