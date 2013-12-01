from __future__ import print_function

import os
import sys
import csv
import StringIO

from collections import namedtuple

from flask import Flask, request, abort
from flask.ext.basicauth import BasicAuth

from boto import connect_route53, connect_s3
from boto.route53.exception import DNSServerError
from boto.s3.key import Key

# Server database management and setup.

DATABASE = {}

def initialise_database():
    global DATABASE

    try:
        data = download_database()
        input = StringIO.StringIO(data)
        reader = csv.reader(input)
        for row in reader:
            hostname, password = row
            DATABASE[hostname] = password
    except Exception:
        DATABASE.clear()
        raise

# Utility functions for interfacing with Amazon services.

def download_database():
    bucket_name = os.environ['DYNDNS_BUCKET']
    connection = connect_s3()
    bucket = connection.get_bucket(bucket_name)
    bucket_data = Key(bucket)
    bucket_data.key = os.environ['DYNDNS_DATABASE']
    return bucket_data.get_contents_as_string()

def upload_database(data):
    bucket_name = os.environ['DYNDNS_BUCKET']
    connection = connect_s3()
    bucket = connection.get_bucket(bucket_name)
    bucket_data = Key(bucket)
    bucket_data.key = os.environ['DYNDNS_DATABASE']
    bucket_data.set_contents_from_string(data)

def register_ip(domain, hostname, ipaddr):
    connection = connect_route53()
    zone = connection.get_zone(domain)
    record = zone.get_a(hostname)

    if record is not None:
        old_ipaddr = record.resource_records[0]

        if old_ipaddr == ipaddr:
            return False

        try:
            zone.update_a(hostname, ipaddr, 300)
        except DNSServerError:
            zone.add_a(hostname, ipaddr, 300)

    else:
        zone.add_a(hostname, ipaddr, 300)

    return True

# Flask application implementing dynamic DNS server.

app = Flask(__name__)
#app.debug = True

class BasicAuthDatabase(BasicAuth):
    def check_credentials(self, username, password):
        if not DATABASE:
            initialise_database()

        if username not in DATABASE:
            return False

        if password != DATABASE[username]:
            return False

        return True

basic_auth = BasicAuthDatabase(app)

@app.route('/register_ip')
@basic_auth.required
def register_ip_handler():
    hostname = request.authorization.username
    domain = '.'.join(hostname.split('.')[1:])

    ipaddr = request.environ.get('HTTP_X_FORWARDED_FOR')
    if not ipaddr:
        ipaddr = request.remote_addr

    register_ip(domain, hostname, ipaddr)

    return ''

@app.route('/check_ip')
def check_ip_handler():
    remote_addr = request.environ.get('HTTP_X_FORWARDED_FOR')
    if not remote_addr:
        remote_addr = request.remote_addr

    return remote_addr

# Command line administration commands.

_commands = {}

def command(name, options='', description='', hidden=False,
        log_intercept=True):
    def wrapper(callback):
        callback.name = name
        callback.options = options
        callback.description = description
        callback.hidden = hidden
        callback.log_intercept = log_intercept
        _commands[name] = callback
        return callback
    return wrapper

def usage(name):
    details = _commands[name]
    print('Usage: dyndns53 %s %s' % (name, details.options))

@command('help', '[command]', hidden=True)
def help(args):
    if not args:
        print('Usage: dyndns53 command [options]')
        print()
        print("Type 'dyndns53 help <command>'", end='')
        print("for help on a specific command.")
        print()
        print("Available commands are:")

        commands = sorted(_commands.keys())
        for name in commands:
            details = _commands[name]
            if not details.hidden:
                print(' ', name)

    else:
        name = args[0]

        if name not in _commands:
            print("Unknown command '%s'." % name, end=' ')
            print("Type 'dyndns53 help' for usage.")

        else:
            details = _commands[name]

            print('Usage: dyndns53 %s %s' % (name, details.options))
            if details.description:
                print()
                print(details.description)

@command('upload-database', 'input_file',
"""Upload the database file to S3.""")
def upload_database_command(args):
    if len(args) == 0:
        usage('upload-database')
        sys.exit(1)

    input_file = args[0]

    with open(input_file, 'r') as input:
        data = input.read()

    upload_database(data)

@command('download-database', '[output_file]',
"""Download the database file from S3.""")
def download_database_command(args):
    if len(args) > 0:
        output_file = args[0]
    else:
        output_file = None

    data = download_database()

    if output_file:
         with open(output_file, 'w') as output:
             output.write(data)
    else:
         print(data)

def main():
    try:
        if len(sys.argv) > 1:
            command = sys.argv[1]
        else:
            command = 'help'

        callback = _commands[command]

    except Exception:
        print("Unknown command '%s'." % command, end='')
        print("Type 'dyndns53 help' for usage.")
        sys.exit(1)

    callback(sys.argv[2:])

# Dynamically determine if being run as admin script or server.

if __name__ == '__main__':
    main()
