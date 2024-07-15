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
    INSERT INTO BaseNote VALUES(5,'NOTE','NOTES','DEFAULT','Note with image',0,1721001532612,'[]',replace('From file system, ~37Kb 1024x1024  PNG\nStored as webp. TODO check if lossless or lossy.','\n',char(10)),'[]','[]','[{"name":"d9f53103-1b01-4936-b62a-5ef87d54791b.webp","mimeType":"image\/webp"}]','[]');
    INSERT INTO BaseNote VALUES(6,'NOTE','NOTES','DEFAULT','Audio note',0,1721001664568,'[]','Quick voice recording. Stores as m4a. TODO codec details.','[]','[]','[]','[{"name":"fdda1ca6-0b0b-4a1e-a2e6-1203497f465e.m4a","duration":2560,"timestamp":1721001688940}]');
    INSERT INTO BaseNote VALUES(8,'NOTE','DELETED','DEFAULT','Deleted note',0,1721005446277,'[]','This note has been deleted.','[]','[]','[]','[]');
    INSERT INTO BaseNote VALUES(9,'NOTE','ARCHIVED','DEFAULT','Archived note',0,1721005471383,'[]','This note is archived.','[]','[]','[]','[]');
    INSERT INTO BaseNote VALUES(10,'NOTE','NOTES','DEFAULT','Styled note',0,1721005515895,'[]',replace('Plain.\nBold\nItalic\nMono-space\nString-Through\nLink\nhttps://google.com\nNot a link https://google.com\nPlain again.','\n',char(10)),'[{"bold":true,"link":false,"italic":false,"monospace":false,"strikethrough":false,"start":7,"end":11},{"bold":false,"link":false,"italic":true,"monospace":false,"strikethrough":false,"start":12,"end":18},{"bold":false,"link":false,"italic":false,"monospace":true,"strikethrough":false,"start":19,"end":29},{"bold":false,"link":false,"italic":false,"monospace":false,"strikethrough":true,"start":30,"end":44},{"bold":false,"link":true,"italic":false,"monospace":false,"strikethrough":false,"start":45,"end":49},{"bold":false,"link":true,"italic":false,"monospace":false,"strikethrough":false,"start":50,"end":68}]','[]','[]','[]');
    INSERT INTO BaseNote VALUES(11,'NOTE','NOTES','DEFAULT','Note with 2 JPEG images',0,1721005791437,'[]',replace('This was originally a JPEG\n16Kb 720x220\n\n2nd also jpeg, ~29Kb 720x449.','\n',char(10)),'[]','[]','[{"name":"403fafef-d171-4718-a0ec-efddd4d5f67b.jpg","mimeType":"image\/jpeg"},{"name":"5764ebcd-97a2-4d04-a335-ffb76285f4af.jpg","mimeType":"image\/jpeg"}]','[]');

    INSERT INTO Label VALUES('Label1');

int/string types, with json for metadata information (todo lists, labels, attachments).
Difference to previous:

  * new columns; images and audios
  * and in the zip file directories for above
      * Audios - filename appears to be UUID of somekind, file extension/type m4a
      * Images - filename appears to be UUID of somekind, file extension/type webp or jpeg (unclear if webp lossless or lossy)

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

