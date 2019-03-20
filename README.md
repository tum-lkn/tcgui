# tcgui

A lightweight Python-based Web-GUI for Linux traffic control (`tc`) to set, view and delete traffic shaping rules. The Web-GUI is intended for short-term isolated testbeds or classroom scenarios and does not contain any security mechanisms.

No further changes are planned right now, but pull requests are welcome.

## Requirements

- Tested with Ubuntu 16.04 LTS & Raspbian 4.14.98-v7+ (stretch, Debian 9.8)
- `netem` tools & `python3-flask` are required
    - Install with `sudo apt-get install iproute python3-flask`
- More information:
    - https://calomel.org/network_loss_emulation.html
    - https://wiki.linuxfoundation.org/networking/netem

## Usage

- Execute the main.py file and go to http://localhost:5000:
    
    ```
    sudo python3 main.py
    
    --ip IP               The IP where the server is listening
    --port PORT           The port where the server is listening
    --dev [DEV [DEV ...]] The interfaces to restrict to
    --regex REGEX         A regex to match interfaces
    --debug               Run Flask in debug mode
    ```

- The tool will read your interfaces and the current setup every time the site is reloaded
