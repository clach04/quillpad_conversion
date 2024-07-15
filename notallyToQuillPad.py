#!/usr/bin/env python3
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
# NOTE Python3 due to use of shutil.unpack_archive()

import sqlite3
import json
import shutil
import os

tags = []
joins = []

# Tested with Notally v5.2 and QuillPad v1.4.9
# will **not** preserve note color
# does **not** handle "attachments"; images and audio/voice recordings

def main():

    tmpFolder = "tmp"  # FIXME pick up using generated temp filename, allowing override via OS environment variables

    quillpadJSON = {"version": "13",
                    "notes": [], "tags": []}

    #notally_export_filename = 'notally.zip'
    notally_export_filename = 'Notally Backup.zip'  # seen 2024-03-18 with version ??? - FIXME argv command line
    # Open a database File
    shutil.unpack_archive(notally_export_filename, tmpFolder)
    db = sqlite3.connect(os.path.join(tmpFolder, 'NotallyDatabase'))
    dbCursor = db.cursor()

    headers = ["ID", "type", "folder", "color", "title", "pinned",
               "timestamp", "labels", "body", "spans", "items"]
    for row in dbCursor.execute("SELECT * FROM BaseNote"):
        note = parseNotallyNote(dict(zip(headers, row)))
        quillpadJSON["notes"].append(note)
    db.close()

    quillpadJSON["tags"] = tags
    quillpadJSON["joins"] = joins

    if not os.path.exists(tmpFolder):
        os.makedirs(tmpFolder)
    with open(os.path.join(tmpFolder, 'backup.json'), 'w') as jsonOut:
        json.dump(quillpadJSON, jsonOut, indent=4)

    os.remove(os.path.join(tmpFolder, 'NotallyDatabase'))
    shutil.make_archive(
        "QuillPadFromNotally", "zip", root_dir=tmpFolder, base_dir=".")
    shutil.rmtree(tmpFolder)


def parseNotallyNote(note):
    noteDict = {}
    noteDict['id'] = note['ID']
    noteDict['title'] = note['title']

    timeStamp = (int)(note['timestamp']/1000)
    noteDict['modifiedDate'] = timeStamp
    noteDict['creationDate'] = timeStamp

    if (note['pinned'] == 1):
        noteDict['isPinned'] = True

    if (note['type'] == "NOTE"):
        noteDict['content'] = note['body']
        noteDict['isMarkdownEnabled'] = False
    elif (note['type'] == "LIST"):
        # body, checked
        lst = json.loads(note['items'])
        outlist = []
        for i, item in enumerate(lst):
            outlist.append(
                {"id": i, "content": item["body"], "isDone": item['checked']})

        noteDict['isList'] = True
        noteDict['taskList'] = outlist

    if (note['folder'] == "DELETED"):
        noteDict['isDeleted'] = True
    elif (note['folder'] == "ARCHIVED"):
        noteDict['isArchived'] = True

    labels = json.loads(note['labels'])
    if len(labels) == 0:
        return noteDict

    noteDict['tags'] = []
    for l in labels:
        hasTag = [t for t in tags if t['name'] == l]
        if len(hasTag) > 0:
            tag = hasTag[0]
        else:
            tag = {"id": len(tags)+1, "name": l}
            tags.append(tag)
        noteDict['tags'].append(tag)
        joins.append(
            {"noteId": noteDict["id"], "tagId": tag['id']})
    return noteDict


if __name__ == "__main__":
    exit(main())

