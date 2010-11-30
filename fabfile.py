from fabric.api import *
import fabric
from fabric.contrib.console import confirm

env.user = 'ubuntu'
env.hosts = ['sugarlog.com']
env.key_filename = '/home/rmobin/.ssh/ec2-sample-key.pem'

def deploy():
    local('git status -s')
    if not confirm('commit above changes?'):
        abort('aborting deploy at your request')
    msg = fabric.operations.prompt('enter the commit message:')
    local('git commit -a -m "%s"' % msg)
    local('git push origin master')
    local('tar czf /tmp/sugarlog.tgz sugarlog.py static templates')
    put('/tmp/sugarlog.tgz', '/tmp/')
    with cd('/mnt/sda/sugarlog'):
        run('sudo tar xzf /tmp/sugarlog.tgz')
        run('cat uwsgi.pid')
        run('sudo kill -HUP `cat uwsgi.pid`')
        run('sleep 2')
        run('tail u.log')
