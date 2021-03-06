from fabric.api import *
import fabric
from fabric.contrib.console import confirm

env.user = 'ubuntu'
env.hosts = ['50.18.57.226']
env.key_filename = '/home/rmobin/.ssh/id_raza-west'
def setup():
    with cd('/usr/src'):
        sudo('add-apt-repository ppa:cherokee-webserver')
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
    # save cherokee config
        sudo('cp /usr/src/sugarlog/server/cherokee.conf /etc/cherokee/cherokee.conf')
        sudo('virtualenv sugarlog')
    with cd('/usr/src/sugarlog'):
    # install pip python libs
        sudo('/usr/src/sugarlog/bin/pip install flask==0.6')
        sudo('/usr/src/sugarlog/bin/pip install py-bcrypt')
    # install redis py
        sudo('git clone git://github.com/andymccurdy/redis-py.git')
    with cd('/usr/src/sugarlog/redis-py'):
        sudo('/usr/src/sugarlog/bin/python setup.py install')
    # use production config (prod redis, etc)
    with cd('/usr/src/sugarlog'):
        sudo('cp /usr/src/sugarlog/server/production.py /usr/src/sugarlog/configmodule.py')
    # restart cherokee so it uses my config
        sudo('/etc/init.d/cherokee restart')
