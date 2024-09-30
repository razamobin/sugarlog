from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, jsonify
import sqlalchemy
from sqlalchemy import text
import datetime
from pytz import timezone
import os
from dotenv import load_dotenv
from datetime import datetime
import re

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'shariq-says-hi'


@app.before_request
def before_request():
    mysql_password = os.getenv('MYSQL_PASSWORD')
    slengine = sqlalchemy.create_engine(
        f'mysql://root:{mysql_password}@localhost:3306/sugarlog',
        poolclass=sqlalchemy.pool.NullPool)
    g.sldb = slengine.connect()


@app.after_request
def after_request(response):
    g.sldb.close()
    return response


@app.route('/')
def slmain():
    # Use `mappings()` to access the result rows as dictionaries
    total = g.sldb.execute(
        text('SELECT COUNT(id) as count FROM posts')).mappings().fetchone()

    skip = int(request.args.get('skip', '0'))

    previous = skip - 10
    if previous < 0:
        previous = None

    next = skip + 10
    if next >= total['count']:
        next = None

    # Fetch rows and access them as dictionaries using `.mappings()`
    rows = g.sldb.execute(
        text(
            'SELECT id, date, blood_sugar, notes FROM posts ORDER BY date DESC, id DESC LIMIT 10 OFFSET :skip'
        ), {
            'skip': skip
        }).mappings().fetchall()

    posts = []
    all_comments = {}
    for r in rows:
        post = {
            'id': r['id'],
            'blood_sugar': r['blood_sugar'],
            'notes': r['notes'],
            'month': r['date'].strftime('%B').lower(),
            'day': day_postfix(r['date'].strftime('%d').lstrip('0'))
        }
        posts.append(post)

        # Fetch comments for each post, safely passing the post ID as a parameter
        comment_rows = g.sldb.execute(
            text('SELECT username, post_id, comment FROM comments c '
                 'LEFT JOIN users u ON c.author_id = u.id '
                 'WHERE post_id = :post_id ORDER BY c.id ASC'), {
                     'post_id': r['id']
                 }).mappings().fetchall()

        post_comments = []
        last_commenter = None
        for cr in comment_rows:
            comment = {'author': cr['username'], 'comment': cr['comment']}
            post_comments.append(comment)
            last_commenter = cr['username']

        post['default_commenter'] = 'raza' if last_commenter in [
            None, 'family'
        ] else 'family'

        if post_comments:
            all_comments[r['id']] = post_comments

    return render_template('slindex.html',
                           posts=posts,
                           comments=all_comments,
                           previous=previous,
                           next=next,
                           title="SugarLog")


@app.route('/slnew', methods=['GET', 'POST'])
def slnew():
    if request.method == 'GET':
        current_date = datetime.now()
        month = current_date.strftime('%B')  # Full month name
        day = current_date.day
        year = current_date.year
        return render_template('slnew.html',
                               year=year,
                               month=month,
                               day=day,
                               title="New Entry")

    #if not 'username' in session:
    #    return redirect(url_for('slmain'))

    month = request.form['month']
    day = request.form['day']
    year = request.form['year']

    #date = datetime.datetime.strptime(month + ' ' + day + ' ' + year, '%B %d %Y')
    #blood_sugar = request.form['blood_sugar']
    #notes = request.form['notes']

    #g.sldb.execute(text("insert into posts (date, blood_sugar, notes) values(%s,%s,%s)", (date, blood_sugar, notes)))

    date = datetime.strptime(f"{month} {day} {year}", '%B %d %Y')
    blood_sugar = request.form['blood_sugar']
    notes = request.form['notes']

    g.sldb.execute(
        text(
            "INSERT INTO posts (date, blood_sugar, notes) VALUES (:date, :blood_sugar, :notes)"
        ), {
            'date': date,
            'blood_sugar': blood_sugar,
            'notes': notes
        })
    g.sldb.commit()

    return redirect(url_for('slmain'))


@app.route('/slcomment', methods=['POST'])
def slcomment():
    author = request.form.get('author')
    comment = request.form.get('comment')
    post_id = request.form.get('post_id')

    # Input validation
    if not all([author, comment, post_id]):
        return jsonify({
            'success': False,
            'error': 'Missing required fields'
        }), 400

    # Check for http or href in comment
    if re.search(r'http|href', comment, re.IGNORECASE):
        return jsonify({
            'success': False,
            'error': 'Comments cannot contain links'
        }), 400

    # Add the comment to the database
    try:
        # Fetch the author_id based on the username
        author_id_result = g.sldb.execute(
            text("SELECT id FROM users WHERE username = :username"), {
                "username": author
            }).fetchone()

        if author_id_result is None:
            return jsonify({'success': False, 'error': 'Invalid author'}), 400

        author_id = author_id_result[0]

        # Insert the comment into the database
        g.sldb.execute(
            text(
                "INSERT INTO comments (post_id, author_id, comment) VALUES (:post_id, :author_id, :comment)"
            ), {
                "post_id": post_id,
                "author_id": author_id,
                "comment": comment
            })
        g.sldb.commit()

        return jsonify({'success': True, 'author': author, 'comment': comment})
    except Exception as e:
        g.sldb.rollback()
        print(f"Error adding comment: {str(e)}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


#@app.route('/raza')
#def raza():
#    session['username'] = 'raza'
#    return redirect(url_for('slmain'))
#
#@app.route('/pervez')
#def pervez():
#    session['username'] = 'pervez'
#    return redirect(url_for('slmain'))


def get_new_post_vars(now=None):
    if not now:
        time_str = '%I.00%p'
        mytz = timezone('US/Pacific')
        now = datetime.datetime.now(mytz)
    else:
        time_str = '%I.%M%p'

    month = datetime.datetime.strftime(now, '%B')
    day = int(datetime.datetime.strftime(now, '%d'))
    year = int(datetime.datetime.strftime(now, '%Y'))
    time = datetime.datetime.strftime(now, time_str).lower().lstrip('0')
    return (month, day, year, time)


def day_postfix(day):
    if day in ['1', '21', '31']:
        return day + 'st'
    elif day in ['2', '22']:
        return day + 'nd'
    elif day in ['3', '23']:
        return day + 'rd'
    else:
        return day + 'th'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
