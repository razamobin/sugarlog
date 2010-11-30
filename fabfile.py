from fabric.api import *

env.user = 'ubuntu'
env.hosts = ['sugarlog.com']
env.key_filename = '/home/rmobin/.ssh/ec2-sample-key.pem'

def deploy():
    local('tar czf /tmp/sugarlog.tgz sugarlog.py static templates')
    put('/tmp/sugarlog.tgz', '/tmp/')
    with cd('/mnt/sda/sugarlog'):
        run('sudo tar xzf /tmp/sugarlog.tgz')
        run('cat uwsgi.pid')
        run('sudo kill -HUP `cat uwsgi.pid`')
        run('sleep 2')
        run('tail u.log')
