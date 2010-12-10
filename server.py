from fabric.api import *
import fabric
from fabric.contrib.console import confirm

env.user = 'ubuntu'
env.hosts = ['ec2-50-16-102-210.compute-1.amazonaws.com']
env.key_filename = '/home/rmobin/.ssh/ec2-sample-key.pem'
def setup():
    with cd('/usr/src'):
        sudo('apt-get update')
        sudo('apt-get install gcc -y')
        sudo('apt-get install libxml2-dev -y')
        sudo('apt-get install python-dev -y')
        sudo('apt-get install gettext -y')
        sudo('apt-get install git-core -y')
        sudo('apt-get install cherokee -y')
        sudo('apt-get install python-virtualenv -y')
        sudo('wget http://projects.unbit.it/downloads/uwsgi-0.9.6.5.tar.gz')
        sudo('tar xvzf uwsgi*.tar.gz')
    with cd('/usr/src/uwsgi*'):
        sudo('make -f Makefile.Py26')
    with cd('/usr/src'):
    # checkout sugar log src
        sudo('git clone git://github.com/razamobin/sugarlog.git')
    # save cherokee config (it should point to proper uwsgi.xml, will update cherokee.conf soon)
        sudo('cp /usr/src/sugarlog/server/cherokee.conf /etc/cherokee/cherokee.conf')
        sudo('virtualenv sugarlog')
    with cd('/usr/src/sugarlog'):
    # install pip python libs
        sudo('/usr/src/sugarlog/bin/pip install flask==0.6')
    # install redis py
        sudo('git clone git://github.com/andymccurdy/redis-py.git')
    with cd('/usr/src/sugarlog/redis-py'):
        sudo('/usr/src/sugarlog/bin/python setup.py install')
    # use production config (prod redis, etc)
    with cd('/usr/src/sugarlog'):
        sudo('cp /usr/src/sugarlog/server/production.py /usr/src/sugarlog/configmodule.py')
    # start cherokee (need to make a nice uwsgi.xml for cherokee to use)
