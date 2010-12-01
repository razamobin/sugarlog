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
    entry_data = g.redis.sort('sugarlog:entries', 0, 1000, 'sugarlog:entry:*->sort',
        ['sugarlog:entry:*->day', 'sugarlog:entry:*->time',
        'sugarlog:entry:*->blood_sugar', 'sugarlog:entry:*->notes'], True)
    for i in range(0, len(entry_data), 4):
        day = day_str(time.strptime(entry_data[i], '%Y-%m-%d'))
        if day in entries:
            day_entries = entries[day]
        else:
            days.append(day)
            day_entries = []
            entries[day] = day_entries;

        day_entries.append({'day' : entry_data[i], 
            'time' : entry_data[i+1], 
            'blood_sugar' : entry_data[i+2], 
            'notes' : entry_data[i+3]}) 

    return render_template('index.html', days=days, entries=entries)

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

def day_str(time_struct):
    s = time.strftime('%B %e', time_struct).lower()
    i = int(re.compile('\s+').split(s)[1]);
    if i in [1,21,31]:
        return s + 'st'
    elif i in [2,22] :
        return s + 'nd'
    elif i in [3,23] :
        return s + 'rd'
    else:
        return s + 'th'

def today_str():
    s = time.strftime('%B %e').lower()
    i = int(re.compile('\s+').split(s)[1]);
    if i in [1,21,31]:
        return s + 'st'
    elif i in [2,22] :
        return s + 'nd'
    elif i in [3,23] :
        return s + 'rd'
    else:
        return s + 'th'

if __name__ == '__main__':
    app.run()
