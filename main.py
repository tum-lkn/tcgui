import subprocess, os, re, argparse
from flask import Flask, render_template, redirect, request, url_for


app = Flask(__name__)
pattern = None
dev_list = None

def parse_arguments():
    parser = argparse.ArgumentParser(description='TC web GUI')
    parser.add_argument('--ip', type=str, required=False,
                        help='The IP where the server is listening')
    parser.add_argument('--port', type=str, required=False,
                        help='The port where the server is listening')
    parser.add_argument('--dev', type=str, nargs='*', required=False,
                        help='The interfaces to restrict to')
    parser.add_argument('--regex',type=str, required=False,
                        help='A regex to match interfaces')
    parser.add_argument('--debug',action='store_true',
                        help='Run Flask in debug mode')
    return parser.parse_args()


@app.route("/")
def main():
    rules = get_active_rules()
    return render_template('main.html', rules=rules)


@app.route('/new_rule/<interface>', methods=['POST'])
def new_rule(interface):
    delay = request.form['Delay']
    loss = request.form['Loss']
    duplicate = request.form['Duplicate']
    reorder = request.form['Reorder']
    corrupt = request.form['Corrupt']
    rate = request.form['Rate']

    # remove old setup
    command = 'tc qdisc del dev %s root netem' % interface
    command = command.split(' ')
    proc = subprocess.Popen(command)
    proc.wait()

    # apply new setup
    command = 'tc qdisc add dev %s root netem' % interface
    if rate != '':
        command += ' rate %smbit' % rate
    if delay != '':
        command += ' delay %sms' % delay
    if loss != '':
        command += ' loss %s%%' % loss
    if duplicate != '':
        command += ' duplicate %s%%' % duplicate
    if reorder != '':
        command += ' reorder %s%%' % reorder
    if corrupt != '':
        command += ' corrupt %s%%' % corrupt
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
        arguments = line.split(' ')
        rule = parse_rule(arguments)
        if rule['name'] and rule['name'] not in dev:
            rules.append(rule)
            dev.add(rule['name'])
    return rules


def parse_rule(splitted_rule):
    rule = {'name':      None,
            'rate':      None,
            'delay':     None,
            'loss':      None,
            'duplicate': None,
            'reorder':   None,
            'corrupt':   None}
    i = 0
    for argument in splitted_rule:
        if argument == 'dev':
            # Both regex pattern and dev name can be given
            # An interface could match the pattern and/or 
            # be in the interface list
            if pattern is None and dev_list is None:
                rule['name'] = splitted_rule[i+1]
            if pattern:
                if pattern.match(splitted_rule[i+1]) :
                    rule['name'] = splitted_rule[i+1]
            if dev_list:
                if splitted_rule[i+1] in dev_list:
                    rule['name'] = splitted_rule[i+1]
        elif argument == 'rate':
            rule['rate'] = splitted_rule[i + 1].split('Mbit')[0]
        elif argument == 'delay':
            rule['delay'] = splitted_rule[i + 1]
        elif argument == 'loss':
            rule['loss'] = splitted_rule[i + 1]
        elif argument == 'duplicate':
            rule['duplicate'] = splitted_rule[i + 1]
        elif argument == 'reorder':
            rule['reorder'] = splitted_rule[i + 1]
        elif argument == 'corrupt':
            rule['corrupt'] = splitted_rule[i + 1]
        i += 1
    return rule


if __name__ == "__main__":
    #if os.geteuid() != 0:
    #    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")
    args = parse_arguments()
    if args.regex:
        pattern = re.compile(args.regex)
    if args.dev:
        dev_list = args.dev
    app_args={}
    if args.ip:
        app_args['host'] = args.ip
    if args.port:
        app_args['port'] = args.port
    if not args.debug:
        app_args['debug'] = False
    app.debug = True
    app.run(**app_args)
