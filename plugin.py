# EPSON Projector control plugin
#
# Author: Romain Rossi <contact@romainrossi.fr>
#
# Based on RAVEn and Base plugins examples from Domoticz (https://github.com/domoticz/domoticz/blob/development/plugins/examples/)
#
# Licence : GPL
#

"""
<plugin key="domoticz_epson_projector" name="Epson Projector" author="Romain Rossi" version="0.0.1" wikilink="https://www.domoticz.com/wiki/Developing_a_Python_plugin" externallink="https://github.com/romainrossi/domoticz-epson-projector">
    <description>
        <h2>Epson Projector</h2><br/>
        This hardware controls an Epson projector using dedicated protocol
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Power control and status on switch (ON/OFF) </li>
            <li>Error status on Alert device</li>
            <li>Serial connection</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Projector : show and controls projector's power state</li>
            <li>Projector Errors : show error status</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li>Serial Port - Configure the serial port connected to the projector</li>
        </ul>
    </description>
    <params>
        <param field="SerialPort" label="Serial Port" width="150px" required="true" default="/dev/ttyUSBx"/>
    </params>
</plugin>
"""
import Domoticz

class EpsonProjectorPlugin:

    SerialConn = None
    Requests = ['PWR?\r','ERR?\r']
    LastRequestIndex = 0
    ErrorMessages = {
          '00' : 'No error',
          '01' : 'Fan error',
          '03' : 'Lamp failure at power on',
          '04' : 'High internal temperature',
          '06' : 'Lamp error',
          '07' : 'Open Lamp cover door error',
          '08' : 'Cinema filter error',
          '09' : 'Electric dual-layered capacitor is disconnected',
          '0A' : 'Auto iris error',
          '0B' : 'Subsystem Error',
          '0C' : 'Low air flow error',
          '0D' : 'Air filter air flow sensor error',
          '0E' : 'Power supply unit error (Ballast)',
          '0F' : 'Shutter error',
          '10' : 'Cooling system error (Peltier element)',
          '11' : 'Cooling system error (Pump)'
    }


    def __init__(self):
        return


    def onStart(self):
        Domoticz.Heartbeat(10) # Set the polling interval
        
        if (len(Devices) != 2):
            # Image : 2=TV
            Domoticz.Device(Name="Projector", Unit=1, TypeName="Switch", Image=2).Create()
            Domoticz.Device(Name="Projector Errors", Unit=2, TypeName="Alert", Image=2).Create()
            Domoticz.Log("Devices created.")

        # Set all devices as TimedOut (red banner)
        for Device in Devices:
            Devices[Device].Update(nValue=Devices[Device].nValue, sValue=Devices[Device].sValue, TimedOut=1)
            self.SerialConn = Domoticz.Connection(Name="epsonproj", Transport="Serial", Protocol="None", Address=Parameters["SerialPort"], Baud=9600)
            self.SerialConn.Connect()


    def onStop(self):
        return


    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Status("Connected successfully to: "+Parameters["SerialPort"])
            self.SerialConn = Connection
        else:
            Domoticz.Error("Failed to connect ("+str(Status)+") to: "+Parameters["SerialPort"]+" with error: "+Description)
        return True


    def onMessage(self, Connection, Data):
        data = Data.decode('utf-8') # Convert from raw byte stream to string
        
        # strip leading ':' and '\r'
        remove = [':','\r']
        for c in remove:
            data = data.replace(c,'')
        
        
        fields = data.split('=',1) # Split the message of format ITEM=val
        if ( len(fields) == 2 ):
            # Handle the various answers
            if fields[0] == 'PWR': # Power status update
                self.UpdatePwrStatus(fields[1])
            elif fields[0] == 'ERR': # Error status update
                self.UpdateErrorStatus(fields[1])
            else:
                Domoticz.Error("Unknown answer received : " + str(Data))
        return


    def onCommand(self, Unit, Command, Level, Hue):
        # Called when switch is actuated in Domoticz
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        if self.SerialConn is None:
            Domoticz.Error("Command requested but serial port not connected")
        elif Unit == 1 :
            if Command=="Off" :
                self.SerialConn.Send("PWR OFF\r")
            elif Command=="On" :
                self.SerialConn.Send("PWR ON\r")
        return


    def onDisconnect(self, Connection):
        for Device in Devices:
            Devices[Device].Update(nValue=Devices[Device].nValue, sValue=Devices[Device].sValue, TimedOut=1)
        Domoticz.Log("Connection '"+Connection.Name+"' disconnected.")
        return


    def onHeartbeat(self):
        # Called every 10 seconds (period can be changed by the Domoticz.Heartbeat(15) command)
        # Poll the projector
        if self.SerialConn is None:
            Domoticz.Error("Serial port not connected")
        else:
            self.LastRequestIndex = self.LastRequestIndex + 1
            if ( self.LastRequestIndex >= len(self.Requests) ):
                self.LastRequestIndex = 0
            self.SerialConn.Send(self.Requests[self.LastRequestIndex])


    def UpdatePwrStatus(self,PwrValue):
        Dev = Devices[1] # Projector domoticz Switch device
        if PwrValue == "00": # Off
            nValue = 0
        elif PwrValue == "01": # On
            nValue = 1
        elif PwrValue == "02": # Warming Up
            nValue = 1
        elif PwrValue == "03": # Cooling Down
            nValue = 0
        elif PwrValue == "05": # Abnormal shutdown
            nValue = 0
        else:
            return
        sValue=''
        TimedOut = 0
        if (Dev.nValue != nValue) or (Dev.sValue != sValue) or (Dev.TimedOut != TimedOut):
            Dev.Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
        return


    def UpdateErrorStatus(self,ErrorValue):
        Dev = Devices[2] # Errors domoticz Alert device
        try:
            sValue = self.ErrorMessages[ErrorValue]
        except KeyError as e:
            Domoticz.Error("Unknown error code received : " + str(ErrorValue))
            sValue = "Unknown Error " + str(ErrorValue)

        # Set Alert color
        if ErrorValue == "00": # No Error => green
            nValue = 1 # nValue==color : 0=grey, 1=green, 2=yellow, 3=orange, 4=red
        else: # Error => Red
            nValue = 4

        TimedOut = 0
        if (Dev.nValue != nValue) or (Dev.sValue != sValue) or (Dev.TimedOut != TimedOut):
            Dev.Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
        return



# Domoticz callbacks boilerplate
global _plugin
_plugin = EpsonProjectorPlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

