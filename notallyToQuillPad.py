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
# does **not** handle "attachments"; images and audio/voice recordings - NOTE does include in new zip file.

"""
Notally 5.4? schema 2023-08-12

    CREATE TABLE android_metadata (locale TEXT);
    CREATE TABLE `BaseNote` (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `type` TEXT NOT NULL, `folder` TEXT NOT NULL, `color` TEXT NOT NULL, `title` TEXT NOT NULL, `pinned` INTEGER NOT NULL, `timestamp` INTEGER NOT NULL, `labels` TEXT NOT NULL, `body` TEXT NOT NULL, `spans` TEXT NOT NULL, `items` TEXT NOT NULL);
    CREATE TABLE `Label` (`value` TEXT NOT NULL, PRIMARY KEY(`value`));
    CREATE TABLE room_master_table (id INTEGER PRIMARY KEY,identity_hash TEXT);


Notally 5.9 schema 2024-07-14

    CREATE TABLE android_metadata (locale TEXT);
    CREATE TABLE `BaseNote` (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `type` TEXT NOT NULL, `folder` TEXT NOT NULL, `color` TEXT NOT NULL, `title` TEXT NOT NULL, `pinned` INTEGER NOT NULL, `timestamp` INTEGER NOT NULL, `labels` TEXT NOT NULL, `body` TEXT NOT NULL, `spans` TEXT NOT NULL, `items` TEXT NOT NULL, `images` TEXT NOT NULL, `audios` TEXT NOT NULL);
    CREATE TABLE `Label` (`value` TEXT NOT NULL, PRIMARY KEY(`value`));
    CREATE TABLE room_master_table (id INTEGER PRIMARY KEY,identity_hash TEXT);

Sample INSERTs/rows:

    INSERT INTO BaseNote VALUES(1,'LIST','NOTES','DEFAULT','Todo list item created 2024-07-14',0,1721001401029,'[]','','[]','[{"body":"Item 1","checked":false},{"body":"Item 2","checked":false},{"body":"Item 3 - checked","checked":true}]','[]','[]');
    INSERT INTO BaseNote VALUES(2,'NOTE','NOTES','DEFAULT','Note created 2024-07-14',0,1721001443718,'[]','Not content.','[]','[]','[]','[]');
    INSERT INTO BaseNote VALUES(3,'NOTE','NOTES','DEFAULT','Pinned note',1,1721001474199,'[]','Content.','[]','[]','[]','[]');
    INSERT INTO BaseNote VALUES(4,'NOTE','NOTES','DEFAULT','Labelled note',0,1721001487017,'["Label1"]',replace('Content here.\nHas Label1.','\n',char(10)),'[]','[]','[]','[]');
    INSERT INTO BaseNote VALUES(5,'NOTE','NOTES','DEFAULT','Note with image',0,1721001532612,'[]','From file system, ~37Kb 1024x1024  PNG.','[]','[]','[{"name":"0fb213bf-9ec1-461f-a167-c8253b2970dc.webp","mimeType":"image\/webp"}]','[]');
    INSERT INTO BaseNote VALUES(6,'NOTE','NOTES','DEFAULT','Audio note',0,1721001664568,'[]','Quick voice recording.','[]','[]','[]','[{"name":"f97c5c17-b824-42dd-ae7a-c26c2b23e942.m4a","duration":2560,"timestamp":1721001688940}]');

    INSERT INTO Label VALUES('Label1');

int/string types, with json for metadata information (todo lists, labels, attachments).
Difference to previous:

  * new columns; images and audios
  * and in the zip file directories for above
      * Audios - filename appears to be UUID of somekind, file extension/type m4a
      * Images - filename appears to be UUID of somekind, file extension/type webp (unclear if lossless or lossy)

"""

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

