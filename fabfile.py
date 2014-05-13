""" Karmaworld Fabric management script
    Finals Club (c) 2013"""

import os
import ConfigParser
from cStringIO import StringIO

from fabric.api import cd, lcd, prefix, run, sudo, task, local, settings
from fabric.state import env as fabenv
from fabric.contrib import files

from dicthelpers import fallbackdict

# Use local SSH config for connections if available.
fabenv['use_ssh_config'] = True

######## env wrapper
# global environment variables fallback to fabric env variables
# (also getting vars will do format mapping on strings with env vars)
env = fallbackdict(fabenv)

######### GLOBALS
env.django_user = '{user}' # this will be different when sudo/django users are
env.group = 'www-data'
env.proj_repo = 'git@github.com:FinalsClub/karmaworld.git'
env.repo_root = '/home/{django_user}/karmaworld'
env.proj_root = '/var/www/karmaworld'
env.branch = 'prod' # only used for supervisor conf two lines below. cleanup?
env.code_root = env.proj_root
env.supervisor_conf = '{code_root}/confs/{branch}/supervisord.conf'
env.usde_csv = '{code_root}/confs/accreditation.csv'

######## Run Commands in Virtual Environment
def virtenv_path():
    """
    Find and memoize the virtualenv for use internally.
    """
    default_venv = env.proj_root + '/venv/bin/activate'

    # Return environment root if its been memoized
    if 'env_root' in env and env['env_root']:
        return env['env_root']

    # Not memoized. Try to find a single unique virtual environment.
    with settings(warn_only=True):
        outp = run("find -L {0} -path '*/bin/activate' | grep -v '/local/'".format(env.proj_root))
    if not len(outp) or len(outp.splitlines()) != 1:
        # Cannot find any virtualenv or found multiple virtualenvs. 
        if len(outp) and default_venv not in outp:
            # Multiple venvs and the default is not present.
            raise Exception('Cannot determine the appropriate virtualenv.')
        # If there are no virtualenvs, then use the default (this will create
        # one if being called by make_virtualenv, otherwise it will cause an
        # error).
        # If there are multiple virtualenvs and the default is in their midst,
        # use the default.
        outp = default_venv
    # Pop off the /bin/activate from /venv/bin/activate
    outp = os.path.sep.join(outp.split(os.path.sep)[:-2])
    env['env_root'] = outp
    return outp

def virtenv_exec(command):
    """
    Execute command in Virtualenv
    """
    with prefix('source {0}/bin/activate'.format(virtenv_path())):
        run(command)

######## Sync database
@task
def syncdb():
    """
    Sync Database
    """
    virtenv_exec('{0}/manage.py syncdb --migrate --noinput'.format(env.code_root))


####### Collect Static Files
@task
def collect_static():
	"""
	Collect static files (if AWS config. present, push to S3)
	"""

	virtenv_exec('{0}/manage.py collectstatic --noinput'.format(env.code_root))

####### Compress Static Files
@task
def compress_static():
	"""
	Compress static files
	"""

	virtenv_exec('{0}/manage.py compress'.format(env.code_root))


####### Run Dev Server
@task
def dev_server():
	"""
	Runs the built-in django webserver
	"""

	virtenv_exec('{0}/manage.py runserver'.format(env.code_root))

####### Create Virtual Environment

@task
def link_code():
    """
    Link the karmaworld repo into the appropriate production location
    """
    if not files.exists(env.code_root):
        run('ln -s {0} {1}'.format(env.repo_root, env.code_root))

@task
def make_virtualenv():
    """
    Create our Virtualenv
    """
    run('virtualenv {0}'.format(virtenv_path()))

@task
def start_supervisord():
    """
    Starts supervisord
    """
    virtenv_exec('supervisord -c {0}'.format(env.supervisor_conf))


@task
def stop_supervisord():
    """
    Restarts supervisord
    """
    virtenv_exec('supervisorctl -c {0} shutdown'.format(env.supervisor_conf))


@task
def restart_supervisord():
    """
    Restarts supervisord, also making sure to load in new config data.
    """
    virtenv_exec('supervisorctl -c {0} update; supervisorctl -c {0} restart all'.format(env.supervisor_conf))


def supervisorctl(action, process):
    """
    Takes as arguments the name of the process as is
    defined in supervisord.conf and the action that should
    be performed on it: start|stop|restart.
    """
    virtenv_exec('supervisorctl -c {0} {1} {2}'.format(env.supervisor_conf, action, process))


@task
def start_celery():
    """
    Starts the celeryd process
    """
    supervisorctl('start', 'celeryd')


@task
def stop_celery():
    """
    Stops the celeryd process
    """
    supervisorctl('stop', 'celeryd')


@task
def restart_celery():
    """
    Restarts the celeryd process
    """
    supervisorctl('restart', 'celeryd')


@task
def start_gunicorn():
    """
    Starts the gunicorn process
    """
    supervisorctl('start', 'gunicorn')


@task
def stop_gunicorn():
    """
    Stops the gunicorn process
    """
    supervisorctl('stop', 'gunicorn')


@task
def restart_gunicorn():
    """
    Restarts the gunicorn process
    """
    supervisorctl('restart', 'gunicorn')

@task
def flush_memcache():
    """
    Clear everything cached in memcached
    """
    virtenv_exec('echo "flush_all" | nc localhost 11211')

####### Update Requirements
@task
def install_reqs():
    # first install must be done without --upgrade for a few packages that break
    # due to a pip problem.
    virtenv_exec('pip install -r {0}/reqs/prod.txt'.format(env.code_root))

@task
def update_reqs():
    # this should generally work to install reqs too, save for a pip problem
    # with a few packages.
    virtenv_exec('pip install --upgrade -r {0}/reqs/prod.txt'.format(env.code_root))

####### Pull new code
@task
def update_code():
    virtenv_exec('cd {0}; git pull'.format(env.code_root))

def backup():
    """
    Create backup using bup
    """
    pass

@task
def file_setup():
    """
    Deploy expected files and directories from non-apt system services.
    """
    ini_parser = ConfigParser.SafeConfigParser()
    # read remote data into a file like object
    data_flo = StringIO(run('cat {supervisor_conf}'.format(**env)))
    ini_parser.readfp(data_flo)
    for section, option in (('supervisord','logfile'),
                            ('supervisord','pidfile'),
                            ('unix_http_server','file'),
                            ('program:celeryd','stdout_logfile')):
      if not ini_parser.has_section(section):
          raise Exception("Could not parse INI file {supervisor_conf}".format(**env))
      filepath = ini_parser.get(section, option)
      # generate file's directory structure if needed
      run('mkdir -p {0}'.format(os.path.split(filepath)[0]))
      # touch a file and change ownership if needed
      if 'log' in option and not files.exists(filepath):
          sudo('touch {0}'.format(filepath))
          sudo('chown {0}:{1} {2}'.format(env.django_user, env.group, filepath))

@task
def check_secrets():
    """
    Ensure secret files exist for syncdb to run.
    """

    secrets_path = env.code_root + '/karmaworld/secret'
    secrets_files = ('filepicker.py', 'static_s3.py', 'db_settings.py', 'drive.py', 'client_secrets.json', 'drive.p12')

    errors = []
    for sfile in secrets_files:
        ffile = os.path.sep.join((secrets_path,sfile))
        if not files.exists(ffile):
            errors.append('{0} missing. Please add and try again.'.format(ffile))
    if errors:
        raise Exception('\n'.join(errors))

@task
def fetch_usde():
    """
    Download USDE accreditation school CSV.
    """
    virtenv_exec('{0}/manage.py fetch_usde_csv {1}'.format(env.code_root, env.usde_csv))

@task
def import_usde():
    """
    Import accreditation school CSV into the database and scrub it.
    """
    virtenv_exec('{0}/manage.py import_usde_csv {1}'.format(env.code_root, env.usde_csv))
    virtenv_exec('{0}/manage.py sanitize_usde_schools'.format(env.code_root))

@task
def first_deploy():
    """
    Sets up and deploys the project for the first time.
    """
    link_code()
    make_virtualenv()
    file_setup()
    check_secrets()
    install_reqs()
    syncdb()
    compress_static()
    collect_static()
    fetch_usde()
    import_usde()
    start_supervisord()
    print "You should run `manage.py createsuperuser` in the virtual environment"


@task
def deploy():
    """
    Deploys the latest changes
    """
    update_code()
    update_reqs()
    syncdb()
    compress_static()
    collect_static()
    restart_supervisord()
########## END COMMANDS
