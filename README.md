# Domoticz Epson Projector Plugin

Plugin to manage an Epson projector from Domoticz using a RS-232 connection.


# Features

- Power control (on/off)
- Power status (is projector on/off ?)
- Errors status reporting in Domoticz

This plugin creates two devices in Domoticz :

1. "Projector" Switch : allows to turn on/off the projector and shows the current state
2. "Projector Error" Alert : provides errors status of the projector


# Supported Devices

Most Epson projector with a serial port should be supported.

| Tested device | Result |
|---|---|---|
| Epson EMP-TW680 | Working |


# Instruction

## Installation

To install this plugin, you need to copy `plugin.py` in the domoticz/plugins/domoticz-epson-projector folder.

    cd domoticz/plugins
    git clone https://github.com/romainrossi/domoticz-epson-projector
    #now restart Domoticz


## Configuration

In Domoticz, go to the "Hardware" page and add a new "Epson projector" hardware.

You need to configure the following parameter :

* "Serial Port" : the RS-232 port to the projector

Click on "Add" to validate the configuration of the new hardware.

If you want to control multiple projectors with the same Domoticz instance, this should work by adding multiple "Epson projector" hardware with different ports. This is untested.


## Usage

After Installation and Configuration are done, two new devices appears (see Features above) so you can :

* Switch On or Off your projector from Domoticz
* Get the power state of the projector (if switched on or off from the remote, the status will be updated in Domoticz)
* Know the error status

From this, you can easilly automate things. Using Domoticz features and scripts, you can

* Switch the lights Off when the projector is turned On from the remote
* Switch off the projector after a long time On
* Send a notification if the projector indicates an error


# Author

Romain Rossi <contact@romainrossi.fr>


# Bug reports, Features requests

Github issues : [https://github.com/romainrossi/domoticz-epson-projector/issues](https://github.com/romainrossi/domoticz-epson-projector/issues)


# Roadmap

- [x] Have a first version working with power control and status
- [x] Add error reporting
- [ ] Add Domoticz Counter showing the lamp hours
- [ ] Add input source control/status

