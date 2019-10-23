import sqlite3
import csv

sqlite3.enable_callback_tracebacks(True)

conn = sqlite3.connect("/tmp/TARS.db")
conn.row_factory = sqlite3.Row

print("Getting list of tags...")

c = conn.cursor()
c.execute('''
    SELECT DISTINCT tag FROM articles_tags
          ''')
tags = [r['tag'] for r in c.fetchall()]

print("Found {} tags!".format(len(tags)))

tags = sorted(tags)
tags = [{'tag': tag, 'articles': 0, 'authors': 0} for tag in tags]

print("Getting article counts...")

for tag in tags:
    c.execute('''
        SELECT article_id FROM articles_tags
        WHERE tag=?
              ''', (tag['tag'],))
    tag['articles'] = len(c.fetchall())

print("Getting author counts...")

for tag in tags:
    c.execute('''
        SELECT DISTINCT author FROM articles_authors
        WHERE article_id IN (SELECT article_id FROM articles_tags
                             WHERE tag=?)
              ''', (tag['tag'], ))
    tag['authors'] = len(c.fetchall())

print("Writing to file...")

with open("tags.csv", 'w') as file:
    csv.DictWriter(file, tags[0].keys()).writerows(tags)
    file.close()

print("All done!")
