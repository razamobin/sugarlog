from fabric.api import *
import fabric
from fabric.contrib.console import confirm

env.user = 'ubuntu'
env.hosts = ['sugarlog.com']
env.key_filename = '/home/rmobin/.ssh/id_raza-west'

def deploy():
    out = local('git status -s')
    print out
    if not confirm('commit above changes?'):
        abort('aborting deploy at your request')
    msg = fabric.operations.prompt('enter the commit message:')
    out = local('git commit -a -m "%s"' % msg)
    print out
    out = local('git push origin master')
    print out
    local('tar czf /tmp/sugarlog.tgz *.py static templates server')
    put('/tmp/sugarlog.tgz', '/tmp/')
    with cd('/usr/src/sugarlog'):
        run('sudo tar xzf /tmp/sugarlog.tgz')
        sudo('cp /usr/src/sugarlog/server/production.py /usr/src/sugarlog/configmodule.py')
        run('cat uwsgi.pid')
        run('sudo kill -HUP `cat uwsgi.pid`')
