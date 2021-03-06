from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
import redis
import json
import time
import datetime
import re
import urllib
import urllib2
import base64
from multiprocessing import Process
import bcrypt

app = Flask(__name__)
app.config.from_object('configmodule.Config')
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=65)

@app.before_request
def before_request():
    g.redis= redis.Redis(host=app.config['REDIS_HOST'], port=int(app.config['REDIS_PORT']))
    g.user = None
    if 'user_id' in session:
        g.user = g.redis.hgetall('sugarlog:uid:%s' % session['user_id'])

@app.after_request
def after_request(response):
    g.redis.connection.disconnect()
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.form.keys():
        username = request.form.get('first_name')
        existing_user = g.redis.get('sugarlog:username:%s:uid' % username)
        if not existing_user:
            # flash message that there is no user
            return render_template('login.html', button='log in', action='/login')

        hashed = g.redis.hget('sugarlog:uid:%s' % existing_user, 'password')
        if not bcrypt.hashpw(request.form.get('password'), hashed) == hashed:
            # flash message that pw doesnt match
            return render_template('login.html', button='log in', action='/login')

        session.permanent = True
        session['user_id'] = existing_user
        #flash("You're now logged in")
        return redirect(url_for('main'))
    else:
        return render_template('login.html', button='log in', action='/login')

@app.route('/logout')
def logout():
    # flash message that you are logged out
    session.pop('user_id', None)
    #flash("You're now logged out")
    return redirect(url_for('main'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.form.keys():
        username = request.form.get('first_name')
        existing_user = g.redis.get('sugarlog:username:%s:uid' % username)
        if existing_user:
            # flash message that user exists already
            return render_template('login.html', button='sign up', action='/signup')
        user = {
            'username' : username,
            'password' : bcrypt.hashpw(request.form.get('password'), bcrypt.gensalt())
        }
        user_id = g.redis.incr('global:next_user_id')
        g.redis.hmset('sugarlog:uid:%s' % user_id, user)
        g.redis.set('sugarlog:username:%s:uid' % username, user_id)
        session.permanent = True
        session['user_id'] = user_id
        # flash message for successful signup
        return redirect(url_for('main'))
    else:
        return render_template('login.html', button='sign up', action='/signup')

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

        entry_id = entry_data[i+4]
        # fetch comments for this entry
        comment_data = g.redis.sort('sugarlog:entry:%s:comments' % entry_id,
            0, 100, 'sugarlog:comment:*->timestamp', 
            ['sugarlog:comment:*->author', 'sugarlog:comment:*->comment'], False)
        last_author = ''
        if comment_data:
            # iterate with steps of 2
            for j in range(0, len(comment_data), 2):
                if entry_id in commentsHash:
                    comments = commentsHash[entry_id]
                else:
                    comments = []
                    commentsHash[entry_id] = comments
                last_author = comment_data[j];
                comments.append({'author' : comment_data[j], 'comment' : comment_data[j+1]})

        pieces = re.compile('\s+').split(day)
        day_entries.append({'day' : entry_data[i], 
            'time' : re.sub("([ap])m.*", "\\1m", entry_data[i+1]).lower().replace('.00', ''), 
            'blood_sugar' : entry_data[i+2], 
            'notes' : entry_data[i+3],
            'entry_id' : entry_data[i+4],
            'month' : pieces[0],
            'day' : pieces[1],
            'next_author' : next_author(last_author)}) 

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
        sms_msg = "new post! dad's blood sugar is %s: http://www.sugarlog.com" % request.form.get('blood_sugar')

        # if not logged in
        if 'user_id' not in session:
            # create user Pervez if dne
            existing_user = g.redis.get('sugarlog:username:%s:uid' % 'Pervez')
            if not existing_user:
                username = 'Pervez'
                user = {
                    'username' : username,
                    'password' : bcrypt.hashpw('', bcrypt.gensalt())
                }
                user_id = g.redis.incr('global:next_user_id')
                g.redis.hmset('sugarlog:uid:%s' % user_id, user)
                g.redis.set('sugarlog:username:%s:uid' % username, user_id)
                existing_user = user_id

            # log in as Pervez
            session.permanent = True
            session['user_id'] = existing_user

        p = Process(target=send_sms, args=(sms_msg,))
        p.start()
        
        return redirect(url_for('main'))
    else:
        return render_template('new.html', user={}, day_display=today_str(), day_input=time.strftime('%Y-%m-%d'))

@app.route('/comments', methods=['POST'])
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
        g.redis.rpush('sugarlog:entry:%s:comments' % request.form.get('entry_id'), comment_id)

        return redirect(url_for('main'))
    else:
        return render_template('comments.html')

def send_sms(message, to='858-663-2602'):
    if app.config['TESTING']:
        return 'testing!'

    username = 'AC42de1d02120c4ee461f62f80a06d81f9'
    password = '4a229a87dd612a30a7cfac5255fe318b'

    post_params = urllib.urlencode({'From' : '858-367-9918', 'To' : to, 'Body' : message})
    request = urllib2.Request('https://api.twilio.com/2010-04-01/Accounts/AC42de1d02120c4ee461f62f80a06d81f9/SMS/Messages')
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)   
    result = urllib2.urlopen(request, post_params)
    return 'done!'

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
    return day_str(time.localtime())

def next_author(last_author):
    if not last_author or last_author == 'Pervez':
        return 'Raza'
    else:
        return 'Pervez'

if __name__ == '__main__':
    app.run()
