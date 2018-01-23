# tcgui

A lightweight Python-based Web-GUI for Linux traffic control (tc) to set, view and delete traffic shaping rules. The Web-GUI is intended for short-term isolated testbeds or classroom scenarios and does not contain any security mechanisms.

No further changes are planned right now, but pull requests are welcome.

## Requirements

- tested with ubuntu 16.04 LTS
- netem tools & python3-flask is required
    - install with `sudo apt-get install iproute python3-flask`
- more information: https://calomel.org/network_loss_emulation.html

## Usage

- Execute the main.py file and go to http://localhost:5000:
    
    sudo python3 main.py

- The tool will read your interfaces and the current setup every time the site is reloaded
