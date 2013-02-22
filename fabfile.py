"""Management utilities."""

import os
from contextlib import contextmanager as _contextmanager

from fabric.api import cd, env, prefix, run, settings, task, local


########## GLOBALS
env.proj_repo = 'git@github.com:FinalsClub/karmaworld.git'
env.virtualenv = 'venv-kw'
env.activate = 'workon %s' % env.virtualenv

# Using this env var to be able to specify the function
# used to run the commands. By default it's `run`, which
# runs commands remotely, but in the `here` task we set
# env.run to `local` to run commands locally.
env.run = run
########## END GLOBALS


########## HELPERS
@_contextmanager
def _virtualenv():
    """
    Changes to the proj_dir and activates the virtualenv
    """
    with cd(env.proj_dir):
        with prefix(env.activate):
            yield

########## END HELPERS

########## ENVIRONMENTS
@task
def here():
    """
    Connection information for the local machine
    """
    env.proj_dir = os.getcwd()
    env.proj_root = os.path.dirname(env.proj_dir)
    env.run = local
    env.reqs = 'reqs/dev.txt'
    env.confs = 'confs/dev/'
    env.branch = 'master'


@task
def beta():
    """
    Beta connection information
    """
    env.user = 'djkarma'
    env.hosts = ['beta.karmanotes.org']
    env.proj_root = '/var/www/karmaworld'
    env.proj_dir = os.path.join(env.proj_root, 'karmaworld')
    env.reqs = 'reqs/prod.txt'
    env.confs = 'confs/beta/'
    env.branch = 'beta'


@task
def prod():
    """
    Production connection information
    """
    env.user = 'djkarma'
    env.hosts = ['karmanotes.org']
    env.proj_root = '/var/www/karmaworld'
    env.proj_dir = os.path.join(env.proj_root, 'karmaworld')
    env.reqs = 'reqs/prod.txt'
    env.confs = 'confs/prod/'
    env.branch = 'master'
########## END ENVIRONMENTS


########## DATABASE MANAGEMENT
@task
def syncdb():
    """Runs syncdb (along with any pending South migrations)"""
    env.run('python manage.py syncdb --noinput --migrate')
########## END DATABASE MANAGEMENT


########## FILE MANAGEMENT
@task
def manage_static():
    collect_static()
    compress_static()
    upload_static()


@task
def collect_static():
    """Collect all static files, and copy them to S3 for production usage."""
    env.run('python manage.py collectstatic --noinput')


@task
def compress_static():
    """
    Compresses the static files.
    """
    pass


@task
def upload_static():
    """
    Uploads the static files to the specified host.
    """
    pass
########## END FILE MANAGEMENT


########## COMMANDS

@task
def make_virtualenv():
    """
    Creates a virtualenv on the remote host
    """
    env.run('mkvirtualenv %s' % env.virtualenv)


@task
def update_reqs():
    """
    Makes sure all packages listed in requirements are installed
    """
    with _virtualenv():
        with cd(env.proj_dir):
            env.run('pip install -r %s' % env.reqs)


@task
def clone():
    """
    Clones the project from the central repository
    """
    env.run('git clone %s %s' % (env.proj_repo, env.proj_dir))


@task
def update_code():
    """
    Pulls changes from the central repo and checks out the right branch
    """
    with cd(env.proj_dir):
        env.run('git pull && git checkout %s' % env.branch)


@task
def deploy():
    """
    Creates or updates the project, runs migrations, installs dependencies.
    """
    first_deploy = False
    with settings(warn_only=True):
        if env.run('test -d %s' % env.proj_dir).failed:
            # first_deploy var is for initial deploy information
            first_deploy = True
            clone()
        if env.run('test -d $WORKON_HOME/%s' % env.virtualenv).failed:
            make_virtualenv()

    update_code()
    update_reqs()
    syncdb()
    #TODO: run gunicorn
    #restart_uwsgi()
########## END COMMANDS
