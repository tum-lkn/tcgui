import subprocess, os
from flask import Flask, render_template, redirect, request, url_for


app = Flask(__name__)


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
    for line in lines:
        arguments = line.split(' ')
        rules.append(parse_rule(arguments))
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
            rule['name'] = splitted_rule[i+1]
        elif argument == 'rate':
            rule['rate'] = splitted_rule[i + 1].split('M')[0]
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
    app.debug = True
    app.run()
