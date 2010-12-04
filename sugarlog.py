from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
import redis
import json
import time
import datetime
import re

DEBUG = True
SECRET_KEY = 'dev key'

app = Flask(__name__)
app.config.from_object(__name__)

@app.before_request
def before_request():
    g.redis= redis.Redis()

@app.after_request
def after_request(response):
    g.redis.connection.disconnect()
    return response

@app.route('/')
def main():
    days = []
    entries = {}
    # map entry ids to list of comment hashes
    commentsHash = {}
    entry_data = g.redis.sort('sugarlog:entries', 0, 1000, 'sugarlog:entry:*->sort',
        ['sugarlog:entry:*->day', 'sugarlog:entry:*->time',
        'sugarlog:entry:*->blood_sugar', 'sugarlog:entry:*->notes', '#'], True)

    for i in range(0, len(entry_data), 5):
        day = day_str(time.strptime(entry_data[i], '%Y-%m-%d'), '%B %e')
        if day in entries:
            day_entries = entries[day]
        else:
            days.append(day)
            day_entries = []
            entries[day] = day_entries;

        pieces = re.compile('\s+').split(day)
        day_entries.append({'day' : entry_data[i], 
            'time' : re.sub("([ap])m.*", "\\1m", entry_data[i+1]), 
            'blood_sugar' : entry_data[i+2], 
            'notes' : entry_data[i+3],
            'entry_id' : entry_data[i+4],
            'month' : pieces[0],
            'day' : pieces[1]}) 

        entry_id = entry_data[i+4]
        # fetch comments for this entry
        comment_data = g.redis.sort('sugarlog:entry:%s:comments' % entry_id,
            0, 100, 'sugarlog:comment:*->timestamp', 
            ['sugarlog:comment:*->author', 'sugarlog:comment:*->comment'], True)
        if comment_data:
            # iterate with steps of 2
            for i in range(0, len(comment_data), 2):
                if entry_id in commentsHash:
                    comments = commentsHash[entry_id]
                else:
                    comments = []
                    commentsHash[entry_id] = comments
                comments.append({'author' : comment_data[i], 'comment' : comment_data[i+1]})

    return render_template('index.html', days=days, entries=entries, commentsHash=commentsHash)

@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.form.keys():
        entry_hash = {
            'sort' : int(time.time()),
            'day' : request.form.get('day'),
            'time' : request.form.get('time'),
            'blood_sugar' : request.form.get('blood_sugar'),
            'notes' : request.form.get('notes')}
            
        # get next entry id
        entry_id = g.redis.incr('global:next_entry_id')

        # create hash entry with all data
        g.redis.hmset('sugarlog:entry:%s' % entry_id, entry_hash)

        # append list of ids
        g.redis.lpush('sugarlog:entries', entry_id)

        return redirect(url_for('main'))
    else:
        return render_template('new.html', user={}, day_display=today_str(), day_input=time.strftime('%Y-%m-%d'))

@app.route('/comments', methods=['GET', 'POST'])
def comments():
    if request.form.keys():
        comment_hash = {
            'timestamp' : int(time.time()),
            'author' : request.form.get('author'),
            'comment' : request.form.get('comment')}
        # get next comment id
        comment_id = g.redis.incr('global:next_comment_id')

        # create hash entry with the comment data
        g.redis.hmset('sugarlog:comment:%s' % comment_id, comment_hash)

        # append list of ids
        g.redis.lpush('sugarlog:entry:%s:comments' % request.form.get('entry_id'), comment_id)

        return redirect(url_for('main'))
    else:
        return render_template('comments.html')

def day_str(time_struct, format='%B %e'):
    s = time.strftime(format, time_struct).lower()
    pieces = re.compile('\s+').split(s)
    if len(pieces) == 2:
        i = int(pieces[1])
    else:
        i = int(pieces[0])
    if i in [1,21,31]:
        return s + 'st'
    elif i in [2,22] :
        return s + 'nd'
    elif i in [3,23] :
        return s + 'rd'
    else:
        return s + 'th'

def today_str():
    return day_str(time.gmtime())

if __name__ == '__main__':
    app.run()
