#!/usr/bin/env python

import datetime
from glob import glob
import os

from fabric.api import *
from fabric import operations
from jinja2 import Template

import app
import app_config
from boto import ses
from etc import github
import pytz
import tumblr_utils

"""
Base configuration
"""
env.deployed_name = app_config.PROJECT_SLUG
env.repo_name = app_config.REPOSITORY_NAME

env.deploy_to_servers = True
env.install_crontab = False
env.deploy_web_services = True

env.repo_url = 'git@github.com:nprapps/%(repo_name)s.git' % env
env.alt_repo_url = None  # 'git@bitbucket.org:nprapps/%(repo_name)s.git' % env
env.user = 'ubuntu'
env.python = 'python2.7'
env.path = '/home/%(user)s/apps/%(deployed_name)s' % env
env.repo_path = '%(path)s/repository' % env
env.virtualenv_path = '%(path)s/virtualenv' % env
env.forward_agent = True

SERVICES = [
    ('app', '%(repo_path)s' % env, 'ini'),
    ('nginx', '/etc/nginx/locations-enabled/', 'conf'),
    ('uwsgi', '/etc/init/', 'conf'),
]

"""
Environments
"""
def production():
    env.settings = 'production'
    env.s3_buckets = app_config.PRODUCTION_S3_BUCKETS
    env.hosts = app_config.PRODUCTION_SERVERS

def staging():
    env.settings = 'staging'
    env.s3_buckets = app_config.STAGING_S3_BUCKETS
    env.hosts = app_config.STAGING_SERVERS

def development():
    env.settings = 'development'
    env.s3_buckets = app_config.STAGING_S3_BUCKETS
    env.hosts = app_config.STAGING_SERVERS

"""
Branches
"""
def stable():
    """
    Work on stable branch.
    """
    env.branch = 'stable'

def master():
    """
    Work on development branch.
    """
    env.branch = 'master'

def branch(branch_name):
    """
    Work on any specified branch.
    """
    env.branch = branch_name

"""
Template-specific functions
"""
def less():
    """
    Render LESS files to CSS.
    """
    for path in glob('less/*.less'):
        filename = os.path.split(path)[-1]
        name = os.path.splitext(filename)[0]
        out_path = 'www/css/%s.less.css' % name

        if os.path.exists('node_modules/.bin/lessc'):
            local('node_modules/.bin/lessc %s %s' % (path, out_path))

        else:
            local('node_modules/bin/lessc %s %s' % (path, out_path))


def jst():
    """
    Render Underscore templates to a JST package.
    """
    if os.path.exists('node_modules/.bin/jst'):
        local('node_modules/.bin/jst --template underscore jst www/js/templates.js')

    else:
        local('node_modules/bin/jst --template underscore jst www/js/templates.js')

def download_copy():
    """
    Downloads a Google Doc as an .xls file.
    """
    base_url = 'https://docs.google.com/spreadsheet/pub?key=%s&output=xls'
    doc_url = base_url % app_config.COPY_GOOGLE_DOC_KEY
    local('curl -o data/copy.xls "%s"' % doc_url)

def update_copy():
    """
    Fetches the latest Google Doc and updates local JSON.
    """
    download_copy()

def app_config_js():
    """
    Render app_config.js to file.
    """
    from app import _app_config_js

    response = _app_config_js()
    js = response[0]

    with open('www/js/app_config.js', 'w') as f:
        f.write(js)

def render():
    """
    Render HTML templates and compile assets.
    """
    from flask import g

    less()
    jst()

    # Fake out deployment target
    app_config.configure_targets(env.get('settings', None))

    app_config_js()

    compiled_includes = []

    for rule in app.app.url_map.iter_rules():
        rule_string = rule.rule
        name = rule.endpoint

        if name == 'static' or name.startswith('_'):
            print 'Skipping %s' % name
            continue

        if rule_string.endswith('/'):
            filename = 'www' + rule_string + 'index.html'
        elif rule_string.endswith('.html'):
            filename = 'www' + rule_string
        else:
            print 'Skipping %s' % name
            continue

        dirname = os.path.dirname(filename)

        if not (os.path.exists(dirname)):
            os.makedirs(dirname)

        print 'Rendering %s' % (filename)

        with app.app.test_request_context(path=rule_string):
            g.compile_includes = True
            g.compiled_includes = compiled_includes

            view = app.__dict__[name]
            content = view()

            compiled_includes = g.compiled_includes

        with open(filename, 'w') as f:
            f.write(content.encode('utf-8'))

    # Un-fake-out deployment target
    app_config.configure_targets(app_config.DEPLOYMENT_TARGET)

def tests():
    """
    Run Python unit tests.
    """
    local('nosetests')

"""
Setup
"""
def setup():
    """
    Setup servers for deployment.
    """
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])

    setup_directories()
    setup_virtualenv()
    clone_repo()
    checkout_latest()
    create_log_file()
    install_requirements()
    install_cairosvg()
    install_pil()

    if env.get('deploy_web_services', False):
        deploy_confs()

def setup_directories():
    """
    Create server directories.
    """
    require('settings', provided_by=[production, staging])

    run('mkdir -p %(path)s' % env)
    run('mkdir -p /var/www/uploads/%s' % app_config.PROJECT_SLUG)
    sudo('chmod -R 777 /var/www/uploads')

def setup_virtualenv():
    """
    Setup a server virtualenv.
    """
    require('settings', provided_by=[production, staging])

    run('virtualenv -p %(python)s --no-site-packages %(virtualenv_path)s' % env)
    run('source %(virtualenv_path)s/bin/activate' % env)

def clone_repo():
    """
    Clone the source repository.
    """
    require('settings', provided_by=[production, staging])

    run('git clone %(repo_url)s %(repo_path)s' % env)

    if env.get('alt_repo_url', None):
        run('git remote add bitbucket %(alt_repo_url)s' % env)

def checkout_latest(remote='origin'):
    """
    Checkout the latest source.
    """
    require('settings', provided_by=[production, staging])
    require('branch', provided_by=[stable, master, branch])

    env.remote = remote

    run('cd %(repo_path)s; git fetch %(remote)s' % env)
    run('cd %(repo_path)s; git checkout %(branch)s; git pull %(remote)s %(branch)s' % env)

def install_requirements():
    """
    Install the latest requirements.
    """
    require('settings', provided_by=[production, staging])

    run('%(virtualenv_path)s/bin/pip install -U -r %(repo_path)s/requirements.txt' % env)

def install_pil():
    """
    On Ubuntu installing encoder support for PIL requires symlinking some libraries.
    """
    require('settings', provided_by=[production, staging])

    sudo('apt-get install -y libjpeg8-dev libfreetype6-dev zlib1g-dev')
    sudo('ln -sf /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/')
    sudo('ln -sf /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/')
    sudo('ln -sf /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/')

def install_crontab():
    """
    Install cron jobs script into cron.d.
    """
    require('settings', provided_by=[production, staging])

    sudo('cp %(repo_path)s/crontab /etc/cron.d/%(deployed_name)s' % env)

def uninstall_crontab():
    """
    Remove a previously install cron jobs script from cron.d
    """
    require('settings', provided_by=[production, staging])

    sudo('rm /etc/cron.d/%(deployed_name)s' % env)

def bootstrap_issues():
    """
    Bootstraps Github issues with default configuration.
    """
    auth = github.get_auth()
    github.delete_existing_labels(auth)
    github.create_default_labels(auth)
    github.create_default_tickets(auth)

def create_log_file():
    """
    Creates the log file for recording Tumblr POSTs.
    """
    sudo('touch /var/log/%s.log' % app_config.PROJECT_SLUG)
    sudo('chown ubuntu /var/log/%s.log' % app_config.PROJECT_SLUG)

def install_scout_plugins():
    """
    Install plugins to Scout.
    """
    with settings(warn_only=True):
        run('ln -s %(repo_path)s/scout/*.rb ~/.scout' % env)

def generate_new_oauth_tokens():
    tumblr_utils.generate_new_oauth_tokens()

def install_cairosvg():
    require('settings', provided_by=[production, staging, development])
    if env.settings == 'development':
        """
        Assumes you're on a Mac.
        Sorry!
        """
        with settings(warn_only=True):
            local('brew install py2cairo')
            prompt('Specify your virtualenv\'s name:', 'virtualenv_name', default="changinglives")
            local('~/.virtualenvs/%(virtualenv_name)s/bin/pip install cairosvg' % env)
            local('ln -s /usr/local/lib/python2.7/site-packages/cairo ~/.virtualenvs/%(virtualenv_name)s/lib/python2.7/site-packages/cairo' % env)

    if env.settings in ['production', 'staging']:
        with settings(warn_only=True):
            sudo('apt-get install -y python-cairo libffi-dev')
            run('%(virtualenv_path)s/bin/pip install cairosvg' % env)
            run('ln -s /usr/lib/python2.7/dist-packages/cairo %(virtualenv_path)s/lib/python2.7/site-packages/cairo' % env)

"""
Deployment
"""
def _deploy_to_s3():
    """
    Deploy the gzipped stuff to S3.
    """
    s3cmd = 's3cmd -P --add-header=Cache-Control:max-age=5 --guess-mime-type --recursive --exclude-from gzip_types.txt sync gzip/ %s'
    s3cmd_gzip = 's3cmd -P --add-header=Cache-Control:max-age=5 --add-header=Content-encoding:gzip --guess-mime-type --recursive --exclude "*" --include-from gzip_types.txt sync gzip/ %s'

    for bucket in env.s3_buckets:
        env.s3_bucket = bucket
        local(s3cmd % ('s3://%(s3_bucket)s/%(deployed_name)s/' % env))
        local(s3cmd_gzip % ('s3://%(s3_bucket)s/%(deployed_name)s/' % env))

def _gzip_www():
    """
    Gzips everything in www and puts it all in gzip
    """
    local('python gzip_www.py')
    local('rm -rf gzip/live-data')

def _render_theme():
    """
    Renders tumblr theme file.
    """
    context = {}

    for config in ['SLUG', 'NAME', 'CREDITS', 'SHORTLINK']:
        config = 'PROJECT_%s' % config
        context[config] = getattr(app_config, config)

    context['SERVERS'] = env.hosts
    context['S3_BUCKET'] = env.s3_buckets[0]

    context['STATIC_URL'] = 'http://127.0.0.1:8000/'
    context['STATIC_CSS'] = '%sless/tumblr.less' % context['STATIC_URL']
    context['STATIC_PRINT_CSS'] = '%sless/tumblr-print.less' % context['STATIC_URL']

    if env.settings in ['production', 'staging']:
        context['STATIC_URL'] = 'http://%s/%s/' % (env.s3_buckets[0], env.deployed_name)
        context['STATIC_CSS'] = '%scss/tumblr.less.css' % context['STATIC_URL']
        context['STATIC_PRINT_CSS'] = '%scss/tumblr-print.less.css' % context['STATIC_URL']

    for TEMPLATE in ['_form.html', '_prompt.html', '_social.html']:
        with open('templates/%s' % TEMPLATE, 'rb') as read_template:
            payload = Template(read_template.read())
            payload = payload.render(context)
            parsed_path = TEMPLATE.split('_')[1].split('.')
            context['%s_%s' % (parsed_path[0].upper(), parsed_path[1].upper())] = payload

    with open('tumblr/theme.html', 'rb') as read_template:
        payload = Template(read_template.read())
        return payload.render(**context)

def write_theme():
    require('settings', provided_by=[production, staging])

    with open('tumblr/rendered-theme.html', 'wb') as write_template:
        write_template.write(_render_theme())

def copy_theme():
    require('settings', provided_by=[production, staging])

    write_theme()
    local('pbcopy < tumblr/rendered-theme.html')

def render_confs():
    """
    Renders server configurations.
    """
    require('settings', provided_by=[production, staging])

    with settings(warn_only=True):
        local('mkdir confs/rendered')

    context = app_config.get_secrets()
    context['PROJECT_SLUG'] = app_config.PROJECT_SLUG
    context['PROJECT_NAME'] = app_config.PROJECT_NAME
    context['REPOSITORY_NAME'] = app_config.REPOSITORY_NAME
    context['CONFIG_NAME'] = app_config.CONFIG_NAME
    context['DEPLOYMENT_TARGET'] = env.settings

    for service, remote_path, extension in SERVICES:
        file_path = 'confs/rendered/%s.%s.%s' % (app_config.PROJECT_SLUG, service, extension)

        with open('confs/%s.%s' % (service, extension),  'r') as read_template:

            with open(file_path, 'wb') as write_template:
                payload = Template(read_template.read())
                write_template.write(payload.render(**context))

def deploy_confs():
    """
    Deploys rendered server configurations to the specified server.
    This will reload nginx and the appropriate uwsgi config.
    """
    require('settings', provided_by=[production, staging])

    render_confs()

    with settings(warn_only=True):
        run('touch /tmp/%s.sock' % app_config.PROJECT_SLUG)
        sudo('chmod 777 /tmp/%s.sock' % app_config.PROJECT_SLUG)

        for service, remote_path, extension in SERVICES:
            service_name = '%s.%s' % (app_config.PROJECT_SLUG, service)
            file_name = '%s.%s' % (service_name, extension)
            local_path = 'confs/rendered/%s' % file_name
            put(local_path, remote_path, use_sudo=True)

            if service == 'nginx':
                sudo('service nginx reload')

            if service == 'uwsgi':
                sudo('initctl reload-configuration')
                sudo('service %s restart' % service_name)

def deploy(remote='origin'):
    """
    Deploy the latest app to S3 and, if configured, to our servers.
    """
    require('settings', provided_by=[production, staging])

    if env.get('deploy_to_servers', False):
        require('branch', provided_by=[stable, master, branch])

    if (env.settings == 'production' and env.branch != 'stable'):
        _confirm("You are trying to deploy the '%(branch)s' branch to production.\nYou should really only deploy a stable branch.\nDo you know what you're doing?" % env)

    render()
    _gzip_www()
    _deploy_to_s3()

    if env.get('deploy_to_servers', False):
        checkout_latest(remote)

        if env.get('install_crontab', False):
            install_crontab()

"""
Tumblr-specific commands.
"""
def analyze_logs():
    """
    Analyzes our tumblr logs to look for over limit errors.
    """
    tumblr_utils.analyze_logs()


def get_logs():
    """
    Grabs log files from remote server for analysis.
    """
    require('settings', provided_by=[production, staging])
    operations.get(app_config.LOG_PATH, app_config.LOG_PATH)


def check_limits():
    """
    Checks our status against Tumblr's post limits.
    """
    tumblr_utils.check_limits()


def write_test_posts():
    """
    Writes test posts to the proper tumblr instance.
    """
    tumblr_utils.write_test_posts()


def write_aggregates():
    """
    Writes an aggregates JSON file to live-data/.
    """
    app_config.configure_targets(env.get('settings', None))
    tumblr_utils.write_aggregates()


def deploy_aggregates():
    """
    Deploys aggregates JSON to S3.
    Calls write_aggregates().
    """
    require('settings', provided_by=[production, staging])
    app_config.configure_targets(env.get('settings', None))
    write_aggregates()
    tumblr_utils.deploy_aggregates(env.s3_buckets)


def send_email():
    """
    Sends a daily email update.
    """
    with app.app.test_request_context():
        payload = app._email()
        addresses = app_config.ADMIN_EMAILS
        connection = ses.connect_to_region('us-east-1')
        connection.send_email(
            'NPR News Apps <nprapps@npr.org>',
            'She Works: %s report' % (datetime.datetime.now(pytz.utc).replace(tzinfo=pytz.utc) - datetime.timedelta(days=1)).strftime('%m/%d'),
            None,
            addresses,
            html_body=payload,
            format='html')


"""
Cron jobs
"""
def cron_test():
    """
    Example cron task. Note we use "local" instead of "run"
    because this will run on the server.
    """
    require('settings', provided_by=[production, staging])

    local('echo $DEPLOYMENT_TARGET > /tmp/cron_test.txt')

"""
Destruction
"""
def _confirm(message):
    answer = prompt(message, default="Not at all")

    if answer.lower() not in ('y', 'yes', 'buzz off', 'screw you'):
        exit()


def nuke_confs():
    """
    DESTROYS rendered server configurations from the specified server.
    This will reload nginx and stop the uwsgi config.
    """
    require('settings', provided_by=[production, staging])

    for service, remote_path in SERVICES:
        with settings(warn_only=True):
            service_name = '%s.%s' % (app_config.PROJECT_SLUG, service)
            file_name = '%s.conf' % service_name

            if service == 'nginx':
                sudo('rm -f %s%s' % (remote_path, file_name))
                sudo('service nginx reload')

            else:
                sudo('service %s stop' % service_name)
                sudo('rm -f %s%s' % (remote_path, file_name))
                sudo('initctl reload-configuration')


def shiva_the_destroyer():
    """
    Deletes the app from s3
    """
    require('settings', provided_by=[production, staging])

    _confirm("You are about to destroy everything deployed to %(settings)s for this project.\nDo you know what you're doing?" % env)

    with settings(warn_only=True):
        s3cmd = 's3cmd del --recursive %s'

        for bucket in env.s3_buckets:
            env.s3_bucket = bucket
            local(s3cmd % ('s3://%(s3_bucket)s/%(deployed_name)s' % env))

        if env.get('deploy_to_servers', False):
            run('rm -rf %(path)s' % env)

            if env.get('deploy_web_services', False):
                nuke_confs()

            if env.get('install_crontab', False):
                uninstall_crontab()
