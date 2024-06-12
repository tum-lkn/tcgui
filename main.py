"""TC web GUI."""

import argparse
import os
import re
import subprocess
import sys

from flask import Flask, redirect, render_template, request, url_for

BANDWIDTH_UNITS = [
    "bit",  # Bits per second
    "kbit",  # Kilobits per second
    "mbit",  # Megabits per second
    "gbit",  # Gigabits per second
    "tbit",  # Terabits per second
    "bps",  # Bytes per second
    "kbps",  # Kilobytes per second
    "mbps",  # Megabytes per second
    "gbps",  # Gigabytes per second
    "tbps",  # Terabytes per second
]

STANDARD_UNIT = "mbit"


app = Flask(__name__)
PATTERN = None
DEV_LIST = None

app.static_folder = "static"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--ip",
        type=str,
        default=os.environ.get("TCGUI_IP"),
        help="The IP where the server is listening",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=os.environ.get("TCGUI_PORT"),
        help="The port where the server is listening",
    )
    parser.add_argument(
        "--dev",
        type=str,
        nargs="*",
        default=os.environ.get("TCGUI_DEV"),
        help="The interfaces to restrict to",
    )
    parser.add_argument(
        "--regex",
        type=str,
        default=os.environ.get("TCGUI_REGEX"),
        help="A regex to match interfaces",
    )
    parser.add_argument("--debug", action="store_true", help="Run Flask in debug mode")
    return parser.parse_args()


@app.route("/")
def main():
    rules = get_active_rules()
    interfaces = get_interfaces()
    return render_template(
        "main.html", rules=rules, units=BANDWIDTH_UNITS, standard_unit=STANDARD_UNIT, interfaces=interfaces
    )


@app.route("/new_rule/<interface>", methods=["POST"])
def new_rule(interface):
    delay = request.form["Delay"]
    delay_variance = request.form["DelayVariance"]
    loss = request.form["Loss"]
    loss_correlation = request.form["LossCorrelation"]
    duplicate = request.form["Duplicate"]
    reorder = request.form["Reorder"]
    reorder_correlation = request.form["ReorderCorrelation"]
    corrupt = request.form["Corrupt"]
    limit = request.form["Limit"]
    rate = request.form["Rate"]
    rate_unit = request.form["rate_unit"]

    interface = filter_interface_name(interface)

    # remove old setup
    command = f"tc qdisc del dev {interface} root netem"
    command = command.split(" ")
    proc = subprocess.Popen(command)
    proc.wait()

    # apply new setup
    command = f"tc qdisc add dev {interface} root netem"
    if rate != "":
        command += f" rate {rate}{rate_unit}"
    if delay != "":
        command += f" delay {delay}ms"
        if delay_variance != "":
            command += f" {delay_variance}ms"
    if loss != "":
        command += f" loss {loss}%"
        if loss_correlation != "":
            command += f" {loss_correlation}%"
    if duplicate != "":
        command += f" duplicate {duplicate}%"
    if reorder != "":
        command += f" reorder {reorder}%"
        if reorder_correlation != "":
            command += f" {reorder_correlation}%"
    if corrupt != "":
        command += f" corrupt {corrupt}%"
    if limit != "":
        command += f" limit {limit}"
    print(command)
    command = command.split(" ")
    proc = subprocess.Popen(command)
    proc.wait()
    return redirect(url_for("main") + "#" + interface)


@app.route("/remove_rule/<interface>", methods=["POST"])
def remove_rule(interface):
    interface = filter_interface_name(interface)

    # remove old setup
    command = f"tc qdisc del dev {interface} root netem"
    command = command.split(" ")
    proc = subprocess.Popen(command)
    proc.wait()
    return redirect(url_for("main") + "#" + interface)


def filter_interface_name(interface):
    return re.sub(r"[^A-Za-z0-9_-]+", "", interface)


def get_active_rules():
    proc = subprocess.Popen(["tc", "qdisc"], stdout=subprocess.PIPE)
    output = proc.communicate()[0].decode()
    lines = output.split("\n")[:-1]
    rules = []
    dev = set()
    for line in lines:
        arguments = line.split()
        rule = parse_rule(arguments)
        if rule["name"] and rule["name"] not in dev:
            rule["ip"] = get_interface_ip(rule["name"])
            rules.append(rule)
            dev.add(rule["name"])
            rules.sort(key=lambda x: x["name"])
    return rules


def get_interfaces():
    proc = subprocess.Popen(["ip", "-o", "-4", "addr", "show"], stdout=subprocess.PIPE)
    output = proc.communicate()[0].decode()
    interfaces = {}
    for line in output.split('\n'):
        if line:
            parts = line.split()
            iface = parts[1]
            ip = parts[3].split('/')[0]
            interfaces[iface] = ip
    return interfaces


def get_interface_ip(interface):
    proc = subprocess.Popen(["ip", "addr", "show", interface], stdout=subprocess.PIPE)
    output = proc.communicate()[0].decode()
    match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', output)
    if match:
        return match.group(1)
    return "No IP found"


def parse_rule(split_rule):
    # pylint: disable=too-many-branches
    rule = {
        "name": None,
        "ip": None,
        "rate": None,
        "delay": None,
        "delayVariance": None,
        "loss": None,
        "lossCorrelation": None,
        "duplicate": None,
        "reorder": None,
        "reorderCorrelation": None,
        "corrupt": None,
        "limit": None,
    }
    i = 0
    for argument in split_rule:
        if argument == "dev":
            # Both regex PATTERN and dev name can be given
            # An interface could match the PATTERN and/or
            # be in the interface list
            if PATTERN is None and DEV_LIST is None:
                rule["name"] = split_rule[i + 1]
            if PATTERN:
                if PATTERN.match(split_rule[i + 1]):
                    rule["name"] = split_rule[i + 1]
            if DEV_LIST:
                if split_rule[i + 1] in DEV_LIST:
                    rule["name"] = split_rule[i + 1]
        elif argument == "rate":
            rule["rate"] = split_rule[i + 1].split("Mbit")[0]
        elif argument == "delay":
            rule["delay"] = split_rule[i + 1]
            if len(split_rule) > (i + 2) and "ms" in split_rule[i + 2]:
                rule["delayVariance"] = split_rule[i + 2]
        elif argument == "loss":
            rule["loss"] = split_rule[i + 1]
            if len(split_rule) > (i + 2) and "%" in split_rule[i + 2]:
                rule["lossCorrelation"] = split_rule[i + 2]
        elif argument == "duplicate":
            rule["duplicate"] = split_rule[i + 1]
        elif argument == "reorder":
            rule["reorder"] = split_rule[i + 1]
            if len(split_rule) > (i + 2) and "%" in split_rule[i + 2]:
                rule["reorderCorrelation"] = split_rule[i + 2]
        elif argument == "corrupt":
            rule["corrupt"] = split_rule[i + 1]
        elif argument == "limit":
            rule["limit"] = split_rule[i + 1]
        i += 1
    return rule


if __name__ == "__main__":
    if os.geteuid() != 0:
        print(
            "You need to have root privileges to run this script.\n"
            "Please try again, this time using 'sudo'. Exiting."
        )
        sys.exit(1)

    # TC Variables
    args = parse_arguments()

    PATTERN = re.compile(args.regex) if args.regex else args.regex
    DEV_LIST = args.dev

    # Flask Variable
    app_args = {"host": args.ip, "port": args.port}
    if not args.debug:
        app_args["debug"] = False
    app.debug = True
    app.run(**app_args)
