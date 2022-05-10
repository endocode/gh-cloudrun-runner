import logging
from logging.config import fileConfig

import os
import sys
import subprocess
import requests
import json
import random
import string

from flask import Flask
from flask import request

fileConfig('logger.cfg')
LOGGER = logging.getLogger()

if 'LOG_LEVEL' in os.environ:
    log_levels = {'NOTSET': 0, 'DEBUG': 10, 'INFO': 20, 'WARN': 30, 'ERROR': 40, 'CRITICAL': 50}
    if os.environ.get('LOG_LEVEL') in log_levels:
        LOGGER.setLevel(log_levels[os.environ.get('LOG_LEVEL')])
    else:
        LOGGER.error(f'LOG_LEVEL {os.environ.get("LOG_LEVEL")} is not a valid level. using {LOGGER.level}')
else:
    LOGGER.warning(f'LOG_LEVEL not set. current log level is {LOGGER.level}')


app_name = 'GitHub Self-Hosted Agent'

app = Flask(app_name)

token = os.environ.get('TOKEN')
organization = os.environ.get('ORGANIZATION')
runner_name_prefix = os.environ.get('NAME')
reg_token = None


def check_system():
    if token is None or organization is None:
        LOGGER.error('GitHub Token and Organization name are required. Cannot proceed without them')
        sys.exit(-1)
    global runner_name_prefix
    if runner_name_prefix is None:
        runner_name_prefix = 'cloudrun-runner'


def get_token():
    registration_token_url = f'https://api.github.com/orgs/{organization}/actions/runners/registration-token'
    headers = {'authorization': f'token ${token}', 'Accept': 'application/vnd.github.v3+json'}
    response = requests.post(url=registration_token_url, headers=headers)
    if response.status_code == 201:
        response_json = json.loads(response.text)
        return response_json['token']


def cleanup():
    LOGGER.info('cleaning up the instance...')
    global reg_token
    cleanup_call = subprocess.run(['sh', 'config.sh', 'remove', '--token', f'{reg_token}'], stdout=subprocess.PIPE)
    LOGGER.info(cleanup_call.stdout)
    reg_token = None


def setup():
    LOGGER.info('setting up the instance...')
    organization_url = f'https://github.com/{organization}'
    runner_name_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    global reg_token
    reg_token = get_token()
    setup_call = subprocess.run(['sh', 'config.sh', '--url', organization_url, '--token', reg_token, '--name',
                                 runner_name_prefix + runner_name_suffix, '--unattended', '--ephemeral',
                                 '--work', '_work'], stdout=subprocess.PIPE)
    LOGGER.info(setup_call.stdout)


def run():
    run_call = subprocess.run(['sh', 'run.sh'], stdout=subprocess.PIPE)
    LOGGER.info(run_call.stdout)


@app.route('/', methods=['GET', 'POST'])
def start():
    if request.method == 'GET':
        return 'Instance is running...', 200
    if request.method == 'POST':
        gh_event = request.headers.get('x-github-event', default=None)
        if gh_event is not None and gh_event == 'workflow_job':
            action = request.json['action']
            if action == 'queued':
                setup()
                run()
                # cleanup is not necessary for ephemeral setup.
                # when the job completes, both the .credentials and .runner files are deleted by default.
                # if you have any specific cleanup tasks to be done, you can include them in the cleanup.
                cleanup()
                return 'All Done!', 201
    return 'Unexpected request', 400


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    check_system()

    from waitress import serve

    serve(app, host='0.0.0.0', port=8080)
