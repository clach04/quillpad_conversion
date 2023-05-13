import sqlite3
import json
import shutil
import os
import tempfile

tags = []
joins = []


def main():

    # Open a database File
    db = sqlite3.connect('NotallyDatabase.db')

    c = db.cursor()

    headers = ["ID", "type", "folder", "color", "title", "pinned",
               "timestamp", "labels", "body", "spans", "items"]
    quillpadJSON = {"version": "13",
                    "notes": [], "tags": []}
    for row in c.execute("SELECT * FROM BaseNote"):
        note = parseNotallyNote(dict(zip(headers, row)))
        if note is not None:
            quillpadJSON["notes"].append(note)
    db.close()

    quillpadJSON["tags"] = tags
    quillpadJSON["joins"] = joins
    
    if not os.path.exists('tmp'):
        os.makedirs('tmp')
    with open('tmp/backup.json', 'w') as jsonOut:
        json.dump(quillpadJSON, jsonOut)
    shutil.make_archive(
        "notallyBackupsInQuill", "zip", root_dir="tmp", base_dir=".")
    shutil.rmtree('tmp')
    print('done reading')


def parseNotallyNote(note):
    noteDict = {}
    noteDict['id'] = note['ID']
    noteDict['title'] = note['title']
    noteDict['modifiedDate'] = note['timestamp']
    noteDict['creationDate'] = note['timestamp']

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
