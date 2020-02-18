import subprocess
import os
import re
import argparse

from flask import Flask, render_template, redirect, request, url_for


BANDWIDTH_UNITS = [
    "bit",   # Bits per second
    "kbit",  # Kilobits per second
    "mbit",  # Megabits per second
    "gbit",  # Gigabits per second
    "tbit",  # Terabits per second
    "bps",   # Bytes per second
    "kbps",  # Kilobytes per second
    "mbps",  # Megabytes per second
    "gbps",  # Gigabytes per second
    "tbps"   # Terabytes per second
]

STANDARD_UNIT = "mbit"


app = Flask(__name__)
pattern = None
dev_list = None


def parse_arguments():
    parser = argparse.ArgumentParser(description='TC web GUI')
    parser.add_argument('--ip', type=str, required=False,
                        help='The IP where the server is listening')
    parser.add_argument('--port', type=int, required=False,
                        help='The port where the server is listening')
    parser.add_argument('--dev', type=str, nargs='*', required=False,
                        help='The interfaces to restrict to')
    parser.add_argument('--regex', type=str, required=False,
                        help='A regex to match interfaces')
    parser.add_argument('--debug', action='store_true',
                        help='Run Flask in debug mode')
    return parser.parse_args()


@app.route("/")
def main():
    rules = get_active_rules()
    return render_template('main.html', rules=rules, units=BANDWIDTH_UNITS,
                           standard_unit=STANDARD_UNIT)


@app.route('/new_rule/<interface>', methods=['POST'])
def new_rule(interface):
    delay = request.form['Delay']
    delay_variance = request.form['DelayVariance']
    loss = request.form['Loss']
    loss_correlation = request.form['LossCorrelation']
    duplicate = request.form['Duplicate']
    reorder = request.form['Reorder']
    reorder_correlation = request.form['ReorderCorrelation']
    corrupt = request.form['Corrupt']
    limit = request.form['Limit']
    rate = request.form['Rate']
    rate_unit = request.form['rate_unit']

    # remove old setup
    command = 'tc qdisc del dev %s root netem' % interface
    command = command.split(' ')
    proc = subprocess.Popen(command)
    proc.wait()

    # apply new setup
    command = 'tc qdisc add dev %s root netem' % interface
    if rate != '':
        command += ' rate %s%s' % (rate, rate_unit)
    if delay != '':
        command += ' delay %sms' % delay
        if delay_variance != '':
            command += ' %sms' % delay_variance
    if loss != '':
        command += ' loss %s%%' % loss
        if loss_correlation != '':
            command += ' %s%%' % loss_correlation
    if duplicate != '':
        command += ' duplicate %s%%' % duplicate
    if reorder != '':
        command += ' reorder %s%%' % reorder
        if reorder_correlation != '':
            command += ' %s%%' % reorder_correlation
    if corrupt != '':
        command += ' corrupt %s%%' % corrupt
    if limit != '':
        command += ' limit %s' % limit
    print(command)
    command = command.split(' ')
    proc = subprocess.Popen(command)
    proc.wait()
    return redirect(url_for('main'))


@app.route('/remove_rule/<interface>', methods=['POST'])
def remove_rule(interface):
    # remove old setup
    command = 'tc qdisc del dev %s root netem' % interface
    command = command.split(' ')
    proc = subprocess.Popen(command)
    proc.wait()
    return redirect(url_for('main'))


def get_active_rules():
    proc = subprocess.Popen(['tc', 'qdisc'], stdout=subprocess.PIPE)
    output = proc.communicate()[0].decode()
    lines = output.split('\n')[:-1]
    rules = []
    dev = set()
    for line in lines:
        arguments = line.split()
        rule = parse_rule(arguments)
        if rule['name'] and rule['name'] not in dev:
            rules.append(rule)
            dev.add(rule['name'])
    return rules


def parse_rule(split_rule):
    rule = {'name':               None,
            'rate':               None,
            'delay':              None,
            'delayVariance':      None,
            'loss':               None,
            'lossCorrelation':    None,
            'duplicate':          None,
            'reorder':            None,
            'reorderCorrelation': None,
            'corrupt':            None,
            'limit':              None}
    i = 0
    for argument in split_rule:
        if argument == 'dev':
            # Both regex pattern and dev name can be given
            # An interface could match the pattern and/or
            # be in the interface list
            if pattern is None and dev_list is None:
                rule['name'] = split_rule[i + 1]
            if pattern:
                if pattern.match(split_rule[i + 1]):
                    rule['name'] = split_rule[i + 1]
            if dev_list:
                if split_rule[i + 1] in dev_list:
                    rule['name'] = split_rule[i + 1]
        elif argument == 'rate':
            rule['rate'] = split_rule[i + 1].split('Mbit')[0]
        elif argument == 'delay':
            rule['delay'] = split_rule[i + 1]
            if len(split_rule) > (i + 2) and 'ms' in split_rule[i + 2]:
                rule['delayVariance'] = split_rule[i + 2]
        elif argument == 'loss':
            rule['loss'] = split_rule[i + 1]
            if len(split_rule) > (i + 2) and '%' in split_rule[i + 2]:
                rule['lossCorrelation'] = split_rule[i + 2]
        elif argument == 'duplicate':
            rule['duplicate'] = split_rule[i + 1]
        elif argument == 'reorder':
            rule['reorder'] = split_rule[i + 1]
            if len(split_rule) > (i + 2) and '%' in split_rule[i + 2]:
                rule['reorderCorrelation'] = split_rule[i + 2]
        elif argument == 'corrupt':
            rule['corrupt'] = split_rule[i + 1]
        elif argument == 'limit':
            rule['limit'] = split_rule[i + 1]
        i += 1
    return rule


if __name__ == "__main__":
    if os.geteuid() != 0:
        print("You need to have root privileges to run this script.\n"
              "Please try again, this time using 'sudo'. Exiting.")
        exit(1)
    args = parse_arguments()
    if args.regex:
        pattern = re.compile(args.regex)
    if args.dev:
        dev_list = args.dev
    app_args = {}
    if args.ip:
        app_args['host'] = args.ip
    if args.port:
        app_args['port'] = args.port
    if not args.debug:
        app_args['debug'] = False
    app.debug = True
    app.run(**app_args)
