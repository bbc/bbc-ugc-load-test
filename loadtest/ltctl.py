#!/usr/bin/env python
"""ltctl - Load Test Control

Usage:
    ./ltctl.py spinup [-n <num>] [-t <type>] [-v]
    ./ltctl.py run <scenario> [-v]
    ./ltctl.py genreport [-v]
    ./ltctl.py uploadreport [-v]
    ./ltctl.py spindown [-v]
    ./ltctl.py status [-v]
    ./ltctl.py createstack [-v]
    ./ltctl.py deletestack [-v]
    ./ltctl.py describestack [-v]
    ./ltctl.py prepare [-v]
    ./ltctl.py release [-v]
    ./ltctl.py cert <cert> [-v]
    ./ltctl.py fetchdependencies [-v]
    ./ltctl.py bandwidth <maxbandwidth> <bandwidthclass> <bandwidthdefaultclass> <port> [-v]
    ./ltctl.py (-h | --help)
    ./ltctl.py --version

Arguments:
    <scenario>  Path to gatling scenario to run. E.g. 'croupier.Ip'.
    <maxbandwidth> The maximum bandwidth
    <bandwidthclass> The restricted bandwidth
    <bandwidthdefaultclass> The rest of the bandwidth
    <port> The port
    <cert> The certificate

Options:
    -n <num>, --number <num>    Number of EC2 instances to spin up [default: 2]
    -t <type>, --type <type>    EC2 Instance Type [default: m4.large]
    -v , --verbose              Print more informational messages.
    -h --help                   Show this screen.
    --version                   Show version.

Examples:
    Spin up 3 large machines for load testing:
        ./ltctl.py spinup -n 3 -t m4.large

    Run a load test:
        ./ltctl.py run croupier.Ip

    'genreport' and 'uploadreport' are only to be used when an error has
    occured during the load test. They are usually called automatically during
    'run'.

        ./ltctl.py genreport "<id>"
"""
from docopt import docopt

import sys

sys.path.append("../infrastructure/src")
# from ..infrastructure.src.ugc.ugcupload import TemplateBuilder

import pickle
from ugc.ugcupload import TemplateBuilder
from os import listdir
from os.path import isfile, join

import os

import shutil
from subprocess import call
from distutils.dir_util import copy_tree
import glob
from boto3 import client
from boto3.s3.transfer import S3Transfer
from botocore.exceptions import NoCredentialsError, ClientError, WaiterError
from click import echo as e
from click import getchar, style, progressbar
from configparser import ConfigParser
from contextlib import contextmanager
from curses import A_BOLD, A_DIM
from curses import wrapper
from datetime import datetime
from functools import wraps

from mimetypes import guess_type
from multiprocessing.dummy import Pool as ThreadPool
from OpenSSL.crypto import Error, FILETYPE_PEM, load_certificate
from os import chdir, getcwd, listdir, makedirs, remove, setpgrp, walk
from os.path import (abspath, basename, dirname, isdir, isfile, join, normpath,
                     realpath, split)
from requests import delete, get, post, put
from shutil import rmtree
from stopit import ThreadingTimeout
import subprocess
from subprocess import CalledProcessError, Popen
from sys import exit
from tailer import tail
from tempfile import TemporaryFile
from time import sleep
from traceback import format_exc

import pprint
import json
import jsonpickle
from cosmosTroposphere import CosmosTemplate

verbose = False
config = ConfigParser(strict=False)
config.read(['ltctl.default.conf', 'ltctl.local.conf'])

cache = {}

# TODO: Normalise these and uppercase
repo_dir = join(dirname(realpath(__file__)), '..')
data_dir = 'data'
remote_log_d = '/var/log/ltctl'


###############################################################################
# UI UTILITIES
###############################################################################
def b(thing_to_print):
    return style(str(thing_to_print), bold=True)


def p_kv(key, val, **kwargs):
    e(str(key) + ': ' + b(val), **kwargs)


def p_quote(text, **kwargs):
    e(style('    > ' + str(text), dim=True), **kwargs)


def p_task(name, **kwargs):
    e(str(name) + ' ', nl=False, **kwargs)


def p_dot(**kwargs):
    e('.', nl=False, **kwargs)


def p_done(**kwargs):
    e('. done!', **kwargs)


def p_complete(**kwargs):
    hr = '-' * 60
    e('\n' + hr + '\nCOMPLETE\n' + hr + '\n', **kwargs)


def p_bullet(thing_to_print, **kwargs):
    e('  * ' + str(thing_to_print), **kwargs)


def p_verbose(thing_to_print, **kwargs):
    if verbose:
        e(style(str(thing_to_print), fg='blue'), err=True, **kwargs)


def prompt_yes(msg):
    e("{0} [y/n]".format(msg), nl=False)
    c = getchar()
    e()
    return c == 'y'


###############################################################################
# UTILITIES
###############################################################################
def bork(msg):
    e(style(msg, fg='red'), err=True)
    exit(1)


def retry_on_exception(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        last_exception = 'None'
        for a in range(200):
            try:
                p_dot()
                r = f(*args, **kwargs)
                p_done()
                return r
            except CalledProcessError as exc:
                last_exception = format_exc()
                last_exception += exc.output
            except Exception:
                last_exception = format_exc()
            p_verbose("Attempt {0}, got exception: {1}".format(
                a, last_exception))
            if (a + 1) % 120 == 0:
                e(b('\n\nINFO: ltctl is still waiting for a condition to '
                    'be reached (waiting for exception to clear):'))
                e(last_exception)
                p_dot()
            sleep(2)
        bork("\n\nGave up: {0}".format(last_exception))

    return wrapped


def conf(key):
    return config.get('ltctl', key)


def get_certificate():
    return (conf('pem_cert'), conf('pem_key'))


def get_email_address():
    with open(conf('pem_cert'), 'r') as buf:
        c = load_certificate(FILETYPE_PEM, buf.read())
    return c.get_subject().emailAddress


def instance_sshname(ip):
    return conf('ssh_format').format(ip=ip, region=conf('region'))


def get_client(service):
    try:
        return cache[service]
    except KeyError:
        cache[service] = client(service, region_name=conf('region'))
        return cache[service]


def get_instances(force_update=False):
    ckey = 'instances_response'
    if force_update or ckey not in cache:
        cache[ckey] = get(conf('cosmos') + '/instances',
                          cert=get_certificate()).json()
    return cache[ckey]


def must_hold(a, description='unknown'):
    p_verbose("Waiting for {0} to hold true, currently: {1}".format(
        description, a))
    if a is True:
        return True
    raise Exception("\nExpected {0} to hold true".format(description))


def must_eql(a, b, description):
    p_verbose("Waiting for {0} '{1}' to equal '{2}'".format(
        description, a, b))
    if a == b:
        return True
    raise Exception("\nExpected {0} to be '{1}' but got '{2}'".format(
        description, b, a))


def run(cmd, **kwargs):
    """A quiet/stderr version of check_output(), only dumping on error."""
    p_verbose("Running: {0}".format(cmd))
    with TemporaryFile(mode='a+') as stdout_f:
        with TemporaryFile(mode='a+') as stderr_f:
            p = Popen(cmd, stdout=stdout_f, stderr=stderr_f, **kwargs)
            retcode = p.wait()
            stdout_f.seek(0)
            stderr_f.seek(0)
            stdout = stdout_f.read()
            stderr = stderr_f.read()
    out = "Process return code: {0}\n".format(retcode)
    out += 'Process stdout:\n'
    out += "\n".join(['   > ' + l for l in stdout.splitlines()])
    out += '\nProcess stderr:\n'
    out += "\n".join(['   > ' + l for l in stderr.splitlines()])
    p_verbose(out)
    if retcode:
        raise CalledProcessError(retcode, cmd, out)
    return stdout, stderr


def ssh(label, run_d, ip, cmd):
    host = instance_sshname(ip)
    out_path = join(run_d, label + '.' + ip + '.stdout')
    out_write = open(out_path, 'a+')
    out_read = open(out_path, 'r')
    err_path = join(run_d, label + '.' + ip + '.stderr')
    err_write = open(err_path, 'a+')
    err_read = open(err_path, 'r')
    ssh_cmd = ['ssh', host, cmd]
    p_verbose("Running: {0}".format(ssh_cmd))
    proc = Popen(ssh_cmd, preexec_fn=setpgrp,
                 stdout=out_write, stderr=err_write)

    sleep(1)

    return {'ip': ip,
            'stdout_fpath': out_path,
            'stdout_write': out_write,
            'stdout_read': out_read,
            'stderr_fpath': err_path,
            'stderr_write': err_write,
            'stderr_read': err_read,
            'process': proc}


def close_ssh(s):
    p_verbose("Closing SSH connection to: {0}".format(s))
    attempt = 0
    while s['process'].poll() is None:
        try:
            if attempt < 10:
                s['process'].terminate()
            else:
                p_kv('Sending SIGKILL to SSH PID', s['process'].pid)
                s['process'].kill()
            attempt += 1
            sleep(1)
        except OSError as e:
            # Only allow OSError: [Errno 3] No such process
            if e.errno != 3:
                p_verbose("[errno 3] No SSH con to: {0}".format(s['ip']))
                raise
    p_verbose("Process return code: {0}".format(s['process'].returncode))
    s['stdout_read'].close()
    s['stderr_write'].close()
    s['stdout_read'].close()
    s['stderr_write'].close()


def mkdir_p(path, *args, **kwargs):
    try:
        return makedirs(path, *args, **kwargs)
    except OSError as e:
        if e.errno != 17:
            raise


def parallel_run(func, instances):
    pool = ThreadPool(min(len(instances), 10))
    results = pool.map(func, instances)
    pool.close()
    pool.join()
    return results


@contextmanager
def cd(path):
    previous_d = getcwd()
    chdir(path)
    try:
        yield
    finally:
        chdir(previous_d)


###############################################################################
# CFN STACK TOOLS
###############################################################################
def from_stack_params(old_params):
    new_p = {}
    for p in old_params:
        new_p[p['ParameterKey']] = p['ParameterValue']
    return new_p


def to_stack_params(p):
    new_vals = [{'ParameterKey': k, 'ParameterValue': v}
                for k, v in p.items() if v is not None]
    old_vals = [{'ParameterKey': k, 'UsePreviousValue': True}
                for k, v in p.items() if v is None]
    return old_vals + new_vals


def describe_stack():
    client = get_client('cloudformation')
    stack_name = conf('stack_name')
    p_verbose("Asking CFN for stack info on: {0}".format(stack_name))
    return client.describe_stacks(StackName=stack_name)['Stacks'][0]


def get_asg():
    cfn_client = get_client('cloudformation')
    p_verbose("Asking CFN for PhysicalResourceId")
    asg_name = cfn_client.describe_stack_resource(
        StackName=conf('stack_name'),
        LogicalResourceId='ComponentAutoScalingGroup'
    )['StackResourceDetail']['PhysicalResourceId']
    asg_client = get_client('autoscaling')
    p_verbose("Asking ASG for info on: {0}".format(asg_name))
    asg = asg_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asg_name])['AutoScalingGroups'][0]
    return asg


def generate_stack_template():
    t = CosmosTemplate(total_az=2, region=conf("region"), description="UgcUpload loadtest",
                       component_name="ugc-upload-load-test-component", project_name='ugc-upload-test')
    TemplateBuilder.buildtemplate(t)
    return t.to_json()


def delete_stack():
    p_task('Deleting stack template')
    try:
        stack = describe_stack()
        cfn_client = get_client('cloudformation')

        response = cfn_client.delete_stack(
            StackName=conf('stack_name'))

        stack_id = pickle.load(open("stack-id.p", "rb"))
        p_dot()
        waiter = cfn_client.get_waiter('stack_delete_complete')
        waiter.wait(StackName=stack_id)
        p_done()

    except ClientError as e:
        bork('Stack does not exist [' + str(e) + "]")


def set_instances(num, type=None):
    cfn_client = get_client('cloudformation')
    p_task("Updating stack to set '{0}' instances of '{1}'".format(num, type))

    # 1) InstanceType must be None if Min/MaxSize is 0
    # 2) Can't just use Cosmos API for updating stack, as you need to supply
    #    the full template and parameters. This includes the ImageId, which I
    #    can't find any Cosmos API that exposes this.

    cfn_client.update_stack(
        StackName=conf('stack_name'),
        UsePreviousTemplate=True,
        Capabilities=['CAPABILITY_IAM'],
        Parameters=to_stack_params({
            'CnameEntry': None,
            'CoreInfrastructureStackName': None,
            'DomainNameBase': None,
            'Environment': None,
            'InstanceType': type,
            'KeyName': None,
            'MaxSize': str(num),
            'MinSize': str(num),
            'DesiredCapacity': str(num),
            'ElbHealthCheckGracePeriod': None,
            'UpdateMaxBatchSize': None,
            'UpdateMinInService': None}))
    p_done()

    p_task('Waiting for CloudFormation stack to update')

    @retry_on_exception
    def _block_until_stack_stable():
        status = describe_stack()['StackStatus']
        must_eql(status, 'UPDATE_COMPLETE', 'stack status')

    sleep(1)
    _block_until_stack_stable()

    p_task("Waiting for ASG to reach '{0}' instances".format(num))

    @retry_on_exception
    def _block_until_instances_ready():
        g = get_asg()
        must_hold(g['MaxSize'] == g['MinSize'] == g['DesiredCapacity'] == num,
                  'stack MaxSize == MinSize == DesiredCapacity == ' + str(num))
        must_eql(len(g['Instances']), num, 'num instances')
        for i in g['Instances']:
            must_eql(i['LifecycleState'], 'InService',
                     'instance lifecycle state')

    _block_until_instances_ready()


def check_asg_not_in_use():
    email = get_email_address()
    instances = get_instances()
    others = set([l['email_address'] for i in instances for l in i['logins']
                  if l['status'] == 'current' and
                  l['email_address'].lower() != email.lower()])
    if others:
        e("The cluster already has '{0}' instances running. In use by:".format(
            len(instances)))
        map(p_bullet, others)
        if not prompt_yes('Proceed even though cluster may be in use?'):
            bork('Exiting on user request')


###############################################################################
# MACHINE LOGIN/CONFIGURATION
###############################################################################
def cosmos_login():
    email = get_email_address()
    login_url = conf('cosmos') + '/logins/create'

    def _active_login(instance):
        if 'logins' in instance:
            return [l for l in instance['logins']
                    if l['status'] == 'current' and
                    l['email_address'].lower() == email.lower()]
        return False

    @retry_on_exception
    def _create_login(instance):
        r = post(login_url, cert=get_certificate(),
                 json={'instance_id': instance['id']})
        r.raise_for_status()
        sleep(0.2)

    with progressbar(get_instances(force_update=True),
                     label='Requesting SSH access') as instances:
        for i in instances:
            if not _active_login(i):
                _create_login(i)

    p_task('Waiting for SSH access to propagate')

    @retry_on_exception
    def _block_until_ssh_ready():
        instances = get_instances(force_update=True)

        def _check_ssh(i):
            must_hold(_active_login(i) is not False, 'cosmos login active')
            host = instance_sshname(i['private_ip_address'])
            cmd = 'cat /proc/loadavg'
            ssh_opts = ['-o', 'ConnectTimeout=2', host, cmd]
            if verbose:
                ssh_opts = ['-vvv'] + ssh_opts
            with ThreadingTimeout(3, swallow_exc=False):
                stdout, _ = run(['ssh'] + ssh_opts)
            p_dot()
            must_hold(len(stdout) >= 3)

        parallel_run(_check_ssh, instances)

    _block_until_ssh_ready()


def configure_machines():
    p_task('Bootstrapping nodes')
    instances = get_instances()

    def _bootstrap(instance):
        host = instance_sshname(instance['private_ip_address'])
        run(['ssh', host, 'rm -rf ~/ec2-package'])
        p_dot()
        run(['scp', '-rp', 'ec2-package', host + ':~/'])
        p_dot()
        run(['ssh', host, '~/ec2-package/tools/configure'])

    parallel_run(_bootstrap, instances)
    p_done()


def kill_test():
    p_task('Stopping test on nodes')
    instances = get_instances()

    def _pkill(instance):
        host = instance_sshname(instance['private_ip_address'])
        run(['ssh', host, 'pkill -INT java'])

    parallel_run(_pkill, instances)
    p_done()


###############################################################################
# GATLING TOOLS
###############################################################################
def run_gatling(scenario, test_id):
    run_d = join(data_dir, test_id, 'tty_outputs')
    mkdir_p(run_d)

    ips = [i['private_ip_address'] for i in get_instances()]
    gat_cmd = "~/ec2-package/tools/run-gatling {0} {1} -s {2}".format(
        test_id, len(ips), scenario)
    gatling_ttys = [ssh('gatling-terminal', run_d, ip, gat_cmd) for ip in ips]
    mon_cmd = '~/ec2-package/tools/sys-info ' + test_id
    loadavg_ttys = [ssh('load-average', run_d, ip, mon_cmd) for ip in ips]

    def _realtime_screen(scr):
        dots = ''
        scr.scrollok(1)
        while None in [c['process'].poll() for c in gatling_ttys]:
            scr.clear()
            scr.addstr('Running gatling scenario: ' + scenario +
                       '. CTRL-C to abort' + dots)
            dots = dots + '.' if len(dots) < 3 else ''
            for c, m in zip(gatling_ttys, loadavg_ttys):
                status = 'running' if c['process'].poll() is None else 'done'
                load = tail(m['stdout_read'], 1)
                load = load[0].strip() if load else '?'
                scr.addstr('\n - ')
                scr.addstr(c['ip'] + ' (' + status + ', loadavg ' + load +
                           '): ', A_BOLD)
                lines = [l for l in tail(c['stdout_read'], 200)
                         if '> Global' in l]
                if lines:
                    c['gatling_started'] = True
                    l = lines[-1].split('(', 1)[1].split(')', 1)[0]
                    scr.addstr(l)
                else:
                    if 'gatling_started' in c and c['gatling_started']:
                        scr.addstr('unknown! High rate of gatling errors?')
                    else:
                        scr.addstr('gatling starting' + dots)
            c = gatling_ttys[0]
            scr.addstr('\n\nLatest stdout from ' + c['ip'] + ':')
            _, width = scr.getmaxyx()
            lim = width - 8
            for l in tail(c['stdout_read'], 20):
                scr.addstr('\n    > ' + l[:lim] + (l[lim:] and '>'), A_DIM)
            scr.refresh()
            sleep(1)

    try:
        wrapper(_realtime_screen)
    except KeyboardInterrupt:
        kill_test()
        p_complete()
        p_task('Closing SSH connections')
        map(close_ssh, loadavg_ttys)
        map(close_ssh, gatling_ttys)
        p_done()
        p_kv('Full gatling terminal stdout/stderr log', run_d)
        p_kv('Run report generation manually using',
             './ltctl genreport "' + test_id + '"')
        bork('Test aborted.')

    p_task('Closing SSH connections used for monitoring')
    map(close_ssh, loadavg_ttys)
    p_done()
    p_complete()
    for c in gatling_ttys:
        if c['process'].returncode != 0:
            e('ERROR: Gatling on ' + c['ip'])
            e('\nLast 20 lines in stdout:')
            map(p_quote, tail(c['stdout_read'], 20))
            e('\nLast 20 lines in stderr:')
            map(p_quote, tail(c['stderr_read'], 20))
            p_kv('\nFull gatling terminal stdout/stderr log', run_d)
            bork('Gatling error above ^^^.')
    p_task('Closing SSH connections used for gatling')
    map(close_ssh, gatling_ttys)
    p_done()


def gen_readme(test_id, instances, dir_to_dump_in):
    README = """
This load test brought to you by ./ltctl

---

Test ID (generated with scenario name and time of test start): {test_id}
Test human: {email}
Number of EC2 instances: {num_instances}
EC2 Instance IDs/IPs:
{instance_list}

---

This directory contains archives from the test run available:

    simulation_logs.tar.bz2

        The raw Gatling simulation logs from each instance that the reports
        were generated from.

    sar_data.tar.bz2

        Binary sar(1) data from each load test instance every 10 seconds for
        the duration of the load test.  To view CPU usage for example:
        cd archive && tar xvfj sar_data.tar.bz2 && sar -u -f sar_data/*.sar.sa

    tty_outputs.tar.bz2

        To run Gatling on each EC2 instance, ltctl maintains an SSH connection
        to run Gatling in the foreground.  The stdout/stderr for this terminals
        are logged and archived here.

    scenarios.tar.bz2

        The Gatling scenarios used in this test run.

    failed_request_logs.tar.bz2

        Gatling debug log of any failed HTTP requests (and their responses)
"""
    keys = ['id', 'instance_type', 'region', 'launch_time',
            'private_ip_address', 'image_id']
    machines = '\n'.join([' -> ' + '/'.join([i[k] for k in keys])
                          for i in instances])
    with open(join(dir_to_dump_in, 'README.txt'), 'w') as f:
        f.write(README.format(
            test_id=test_id,
            email=get_email_address(),
            num_instances=len(instances),
            instance_list=machines))


def gen_report(test_id):
    results_d = join(data_dir, test_id, 'results')
    sim_log_d = join(data_dir, test_id, 'simulation_logs')
    sar_d = join(data_dir, test_id, 'sar_data')
    failed_req_d = join(data_dir, test_id, 'failed_request_logs')
    archive_d = join(results_d, 'archive')
    print(list(map(mkdir_p, [results_d, sim_log_d, sar_d, failed_req_d, archive_d])))
    instances = get_instances()
    with progressbar([i['private_ip_address'] for i in instances],
                     label='Downloading test data from instances') as ips:
        for ip in ips:
            host = instance_sshname(ip)
            rmt_sim = "{0}:{1}/gatling/{2}*/simulation.log".format(
                host, remote_log_d, test_id.split(".")[-1].lower())
            lcl_sim_path = join(results_d, ip) + '.simulation.log'
            run(['scp', '-C', rmt_sim, lcl_sim_path])

            rmt_sa_path = "{0}:{1}/sar/{2}.sar.sa".format(
                host, remote_log_d, test_id)
            lcl_sar_path = join(sar_d, ip) + '.sar.sa'
            run(['scp', '-C', rmt_sa_path, lcl_sar_path])

            rmt_fl_path = "{0}:{1}/log/failed_req.{2}.log".format(
                host, remote_log_d, test_id)
            lcl_fl_path = join(failed_req_d, ip) + '.log'
            run(['scp', '-C', rmt_fl_path, lcl_fl_path])

    gat_dir = '.gatling'
    if not isdir(gat_dir):
        p_task('Installing gatling on local machine for report creation')
        run(['make', 'SOURCES'], cwd=repo_dir)
        run(['cp', 'SOURCES/gatling.zip', 'loadtest/'], cwd=repo_dir)
        run(['unzip', 'gatling.zip'])
        remove('gatling.zip')
        run('mv gatling-charts-highcharts-bundle-* ' + gat_dir, shell=True)
        p_done()

    p_task('Generating gatling report - this can take a long time')
    # TODO: Get gatling using appropriate amount of memory
    run(['.gatling/bin/gatling.sh', '-ro', abspath(results_d)])
    p_done()

    def _archive_d(dir, rm=False):
        print("location["+str(dir))

        d_head, d_tail = split(dir)
        print("head["+d_head)
        assert (d_tail is not None)
        p_task("Compressing {0} (this can take a long time)".format(d_tail))
        pkg = abspath(join(archive_d, d_tail + '.tar.bz2'))
        run(['tar', '-jcvf', pkg, d_tail], cwd=d_head)
        if rm:
            rmtree(dir)
        p_done()

    run('mv *.simulation.log ' + abspath(sim_log_d), cwd=results_d, shell=True)
    # _archive_d(sim_log_d, rm=True)
    # _archive_d(join(data_dir, test_id, 'tty_outputs'), rm=True)
    # _archive_d(join('ec2-package', 'scenarios'))
    # _archive_d(sar_d, rm=True)
    # _archive_d(failed_req_d, rm=True)

    gen_readme(test_id, instances, archive_d)
    p_complete()
    p_kv('Local dir', results_d)

    if prompt_yes('Upload gatling report to S3?'):
        upload_report(test_id)
    else:
        p_kv('Upload to S3 manually with',
             './ltctl uploadreport "' + test_id + '"')


def upload_report(test_id):
    results_d = join(data_dir, test_id, 'results')
    tf = S3Transfer(get_client('s3'))
    s3_pfx = 'ltctl/' + test_id
    with cd(results_d):
        all_files = [join(d_path, f)
                     for d_path, _, f_names in walk('.')
                     for f in f_names]
        with progressbar(all_files, label='Uploading ' + results_d) as files:
            for path in files:
                mime, _ = guess_type(path)
                mime = mime if mime else 'application/octet-stream'
                key = normpath(join(s3_pfx, path))
                tf.upload_file(path, conf('results_bucket'), key,
                               extra_args={'ContentType': mime})
    p_complete()
    p_bullet('Test archives: ' + b(
        "http://{0}.s3-website-{1}.amazonaws.com/{2}{3}".format(
            conf('results_bucket'), conf('region'), s3_pfx,
            '/archive/README.txt')))
    p_bullet('Results URL: ' + b(
        "http://{0}.s3-website-{1}.amazonaws.com/{2}".format(
            conf('results_bucket'), conf('region'), s3_pfx)))


###############################################################################
# STATUS REPORTING
###############################################################################
def status():
    stack = describe_stack()
    params = from_stack_params(stack['Parameters'])
    asg = get_asg()
    assert (asg['MaxSize'] == asg['MinSize'] == asg['DesiredCapacity'])

    p_kv('CFN stack status', stack['StackStatus'])
    p_kv('EC2 instance type', params['InstanceType'])
    p_kv('ASG desired capacity', asg['DesiredCapacity'])
    e('EC2 instances:')
    instances = get_instances()
    if instances:
        for i in instances:
            p_bullet(i['id'] + ': ' + i['private_ip_address'] + ',' +
                     i['region'])
    else:
        p_bullet('<none running>')


def preflight_checks():
    p_task('Testing access to cosmos and AWS APIs')
    try:
        get_email_address()
    except IOError as e:
        if e.errno == 2:
            bork('Certificate configured in lctcl.{default,local}.conf ' +
                 'does not exist.')
    except Error:
        bork('Certificate configured in lctcl.{default,local}.conf ' +
             'cannot be read.')

    try:
        get_asg()
    except NoCredentialsError:
        bork('AWS credentials not found. ' +
             'Have they been configured in ~/.aws/credentials ?')
    except ClientError:
        bork('ClientError when contacting AWS. ' +
             'Has the wrong account been configured in ~/.aws/credentials, ' +
             'or the incorrect stack name configured?')
    p_done()


###############################################################################
# UGC- Setting up Test Environment
###############################################################################

def download_test_data():
    p_task('download test data')
    instances = get_instances()

    def _bootstrap(instance):
        host = instance['private_ip_address']
        cmd = 'aws s3 sync ' + conf('testdata') + ' ~/gatling/user-files/data'
        ssh('download_test_data', '/tmp', host, cmd)
        p_dot()

    parallel_run(_bootstrap, instances)
    p_done()


def upload_cert():
    p_task('Uploading certificate')
    instances = get_instances()

    def _bootstrap(instance):
        host = instance_sshname(instance['private_ip_address'])
        run(['scp', '-rp', conf('certlocation'), host + ':~/'])
        ssh('moving_bbc_cert','/tmp', instance['private_ip_address'], 'sudo cp ~/*.p12 /opt/gatling/')
        ssh('change_owner_bbc_cert','/tmp', instance['private_ip_address'], 'sudo chown -R "$USER"  /opt/gatling/*.p12')
        p_dot()

    parallel_run(_bootstrap, instances)
    p_done()


def limit_bandwidths(max_bandwidth, bandwidth_class, bandwidth_default, port):
    p_task('Limiting bandwidth')
    instances = get_instances()

    def _limit_bandwidth(instance):
        host = instance['private_ip_address']
        ssh('setting_up_ip_forward', '/tmp', host, 'sudo sysctl net.ipv4.ip_forward')
        p_dot()
        ssh('forward_91_443', '/tmp', host,
            'sudo iptables -t nat -A OUTPUT -p tcp --dport ' + port + ' -j DNAT --to ' + conf('systemundertest'))
        p_dot()
        ssh('set_mark', '/tmp', host,
            'sudo iptables -I OUTPUT -t mangle -p tcp --dport ' + port + ' -j MARK --set-mark 1')
        p_dot()
        ssh('root_qdisc', '/tmp', host, 'sudo tc qdisc add dev eth0 root handle 1: htb default 1')
        p_dot()
        ssh('root_class', '/tmp', host, 'sudo tc class add dev eth0 parent 1:0 classid 1:1 htb rate ' + max_bandwidth)
        p_dot()
        ssh(bandwidth_class + '_class', '/tmp', host,
            'sudo tc class add dev eth0 parent 1:1 classid 1:10 htb rate ' + bandwidth_class + ' ceil ' + bandwidth_class)
        p_dot()
        ssh(bandwidth_default + '_class', '/tmp', host,
            'sudo tc class add dev eth0 parent 1:1 classid 1:11 htb rate ' + bandwidth_default + ' ceil ' + max_bandwidth)
        p_dot()
        ssh('sfq_' + bandwidth_class + '_class', '/tmp', host,
            'sudo tc qdisc add dev eth0 parent 1:10 handle 10: sfq perturb 5')
        p_dot()
        ssh('filter_' + bandwidth_class + '_class', '/tmp', host,
            'sudo tc filter add dev eth0 parent 1:0 prio 1 protocol ip handle 1 fw flowid 1:10')

    parallel_run(_limit_bandwidth, instances)
    p_done()


def create_stack():
    register_template()
    register_stack_with_cosmos()
    register_main_stack()


def register_template():
    p_task('Creating stack template')
    try:
        stack = describe_stack()
        bork('Stack Already exists.')
    except ClientError as e:
        cfn_client = get_client('cloudformation')
        response = cfn_client.create_stack(
            StackName=conf('stack_name'),
            Capabilities=['CAPABILITY_NAMED_IAM'],
            TemplateBody=generate_stack_template(),
            Parameters=to_stack_params({
                'CnameEntry': 'ugc-loadtest.int',
                'CoreInfrastructureStackName': 'core-infrastructure',
                'DomainNameBase': 'c7dff5ab13c48206.xhst.bbci.co.uk.',
                'Environment': 'int',
                'InstanceType': 't2.micro',
                'KeyName': 'cosmos',
                'MaxSize': '0',
                'MinSize': '0',
                'DesiredCapacity': '0',
                'UpdateMaxBatchSize': '1',
                'ElbHealthCheckGracePeriod': '30000',
                'UpdateMinInService': '0'}),
            OnFailure='ROLLBACK'
        )

        pickle.dump(response['StackId'], open("stack-id.p", "wb"))
        waiter = cfn_client.get_waiter('stack_create_complete')
        waiter.wait(StackName=response['StackId'])

    p_done()


def unregister_stack():
    jd = {"remove_from_aws": False}
    json_data = json.dumps(jd)

    headers = {'Content-Type': 'application/json'}
    res = delete(
        conf('cosmosBaseUrl') + '/v1/services/' + conf('cosmoscomponent') + '/int/stacks/' + conf('stack_name'),
        json=jd, cert=get_certificate(), headers=headers)

    if (res.status_code == 400):
        print("unable to unregister the stack [" + str(res.content))


def register_main_stack():
    mainStack = conf('stack_name')
    jd = {'value': mainStack}
    json_data = json.dumps(jd)

    headers = {'Content-Type': 'application/json'}
    res = put(conf('cosmosBaseUrl') + '/v1/services/' + conf('cosmoscomponent') + '/int/main_stack',
              json=jd, cert=get_certificate(), headers=headers)

    if (res.status_code == 400):
        print("uable to set main stack [" + str(res.content))


def register_stack_with_cosmos():
    jd = {'aws_account': conf('awsaccount'), 'region': conf('region')}
    json_data = json.dumps(jd)
    headers = {'Content-Type': 'application/json'}

    res = put(conf('cosmosBaseUrl') + '/v1/services/' + conf('cosmoscomponent') + '/int/stacks/' + conf('stack_name'),
              json=jd, cert=get_certificate(), headers=headers)

    if (res.status_code == 400):
        print("uable to register stack")


def get_latest_release():
    res = get(conf('cosmosBaseUrl') + '/v1/services/ugc-loadtest/releases',
              cert=get_certificate())

    return str(res.json()['releases'][0]['version'])


def release_latest():
    latest_release = get_latest_release()
    json_data = {'release_version': latest_release}

    headers = {'Content-Type': 'application/json'}

    res = post(conf('cosmosBaseUrl') + '/env/int/component/ugc-loadtest/deploy_release',
               json=json_data, cert=get_certificate(), headers=headers)

    if (res.status_code == 400):
        print("uable to do the latest release[" + str(res.content) + "]")


def release():
    release_latest()


def fetch_dependencies():
    p_task('Fetch dependencies')
    instances = get_instances()

    def _fetch_dependencies(instance):
        host = instance['private_ip_address']

        dependencies = config.items('jars')
        for dependency in dependencies:
            loc = dependency[1]
            ele = dependency[1]
            jar = ele.split("/")[-1]
            ssh('fetch_' + jar + '_' + host, '/tmp', host, 'sudo curl -o /opt/gatling/lib/' + jar + ' ' + loc)
            ssh('fetch_change_permission' + jar + '_' + host, '/tmp', host, 'sudo chown -R "$USER" /opt/gatling/lib/' + jar)
        p_dot()

    parallel_run(_fetch_dependencies, instances)
    p_done()


def update_test_files():
    dirpath = os.getcwd()
    fromDirectory = conf('gatlingtestsrc') + "/test/scala/"
    toDirectory = dirpath + "/ec2-package/scenarios"

    call(['rm', '-rf', toDirectory + "/*"])
    call(['cp', '-r', fromDirectory, toDirectory])


if __name__ == '__main__':
    args = docopt(__doc__, version='Load Test Control 0.1')
    verbose = args['--verbose']

    if args['fetchdependencies']:
        fetch_dependencies()

    if args['cert']:
        upload_cert(conf('certlocation'))

    if args['release']:
        release()

    if args['describestack']:
        print(str(describe_stack()['StackStatus']))

    if args['deletestack']:
        delete_stack()
        unregister_stack()

    if args['createstack']:
        create_stack()

    if args['prepare']:
        update_test_files()
        # preflight_checks()
        # subprocess.call("./prepare.sh")

    if args['bandwidth']:
        preflight_checks()
        maxbandwidth = args['<maxbandwidth>']
        bandwidthclass = args['<bandwidthclass>']
        bandwidthdefaultclass = args['<bandwidthdefaultclass>']
        port = args['<port>']

        limit_bandwidths(maxbandwidth, bandwidthclass, bandwidthdefaultclass, port)

    if args['status']:
        preflight_checks()
        status()

    if args['spinup']:
        preflight_checks()
        check_asg_not_in_use()
        num_instances = int(args['--number'])
        set_instances(num_instances, args['--type'])
        with progressbar(range(20),
                         label='Allowing time for sshd to start') as seconds:
            for _ in seconds:
                sleep(1)
        cosmos_login()
        # release_latest()
        p_complete()
        p_kv('When ready, run', './ltctl run <scenario>')
        p_kv('For example', './ltctl run "croupier.Ip"')

    if args['run']:
        preflight_checks()
        spath = join('ec2-package', 'scenarios')
        spath = join(spath, *args['<scenario>'].split('.')) + '.scala'
        update_test_files()

        # This abomination is to work around case-aware HFS
        if basename(spath) not in listdir(dirname(spath)) or not isfile(spath):
            bork('Could not find Gatling scenario: ' + spath)

        check_asg_not_in_use()

        cosmos_login()
        configure_machines()
        fetch_dependencies()
        download_test_data()
        upload_cert()

        test_id = "{0}.{1}".format(
            datetime.now().strftime('%Y-%m-%d.%H-%M-%S'), args['<scenario>'])

        pickle.dump(test_id, open("test-id.p", "wb"))
        p_kv('Test id', test_id)
        run_gatling(args['<scenario>'], test_id)
        gen_report(test_id)

    if args['genreport']:
        preflight_checks()
        check_asg_not_in_use()
        cosmos_login()
        test_id = pickle.load(open("test-id.p", "rb"))
        # gen_report(args['<test_id>'])
        gen_report(test_id)

    if args['uploadreport']:
        preflight_checks()
        test_id = pickle.load(open("test-id.p", "rb"))
        upload_report(test_id)

    if args['spindown']:
        preflight_checks()
        check_asg_not_in_use()
        set_instances(0)
