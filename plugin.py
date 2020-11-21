# EPSON Projector control plugin
#
# Author: Romain Rossi <contact@romainrossi.fr>
#
# Based on RAVEn and Base plugins examples from Domoticz (https://github.com/domoticz/domoticz/blob/development/plugins/examples/)
#
# Licence : GPL
#

"""
<plugin key="domoticz_epson_projector" name="Epson Projector" author="Romain Rossi" version="0.1.0" wikilink="https://www.domoticz.com/wiki/Developing_a_Python_plugin" externallink="https://github.com/romainrossi/domoticz-epson-projector">
    <description>
        <h2>Epson Projector</h2><br/>
        This hardware controls an Epson projector using dedicated protocol
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Power control and status on Switch Device (ON/OFF) </li>
            <li>Error status on Alert Device</li>
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
            <li>Polling Period - Configure the polling interval (seconds)</li>
        </ul>
    </description>
    <params>
        <param field="SerialPort" label="Serial Port" width="150px" required="true" default="/dev/ttyUSBx"/>
        <param field="Port" label="Polling Period (s)" width="150px" required="true" default="15"/>
    </params>
</plugin>
"""
import Domoticz

class EpsonProjectorPlugin:

    SerialConn = None
    Requests = {
        "Power": 'PWR?\r',
        "Error": 'ERR?\r',
        "Lamp": 'LAMP?\r'
    }
    ProjectorOn = False
    RequestsList = ["Power"]
    RequestsListOn = ["Power", "Error", "Lamp"]
    RequestsListOff = ["Power", "Lamp"]
    Received = ''
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
        Domoticz.Status("Setting polling period : "+Parameters["Port"]+"s")
        Domoticz.Heartbeat(int(Parameters["Port"])) # Set the polling interval

        if (len(Devices) < 3):
            # Image : 2=TV
            Domoticz.Device(Name="Projector", Unit=1, TypeName="Switch", Image=2).Create()
            Domoticz.Device(Name="Projector Errors", Unit=2, TypeName="Alert").Create()
            Domoticz.Device(Name="Projector Lamp Hours", Unit=3, TypeName="Custom", Options={"Custom": "1;Hours"}).Create()
            #Domoticz.Device(Name="Projector Lamp Hours", Unit=3, Type=243, Subtype=33, Switchtype=5).Create() # Create a General(243) Managed Counter(33) of Time(5)
            Domoticz.Status("Devices created.")

        # Set all devices as TimedOut (red banner)
        for Device in Devices:
            Devices[Device].Update(nValue=Devices[Device].nValue, sValue=Devices[Device].sValue, TimedOut=1)
            self.SerialConn = Domoticz.Connection(Name="epsonproj", Transport="Serial", Protocol="Line", Address=Parameters["SerialPort"], Baud=9600)
            self.SerialConn.Connect()

    def onStop(self):
        Domoticz.Status("Stopping")
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
        data = data.replace('\r',':') # Strip \r
        self.Received += data # Add new message to previously incomplete message
        Domoticz.Log("Received:"+self.Received)
        try:
            msgs = self.Received.split(':') # Split each message
        except ValueError:
            pass
        self.Received = '' # Clean incomplete message storage
        nb_msgs = len(msgs)
        for i in range(nb_msgs):
            m = msgs[i]
            fields = m.split('=') # Split the message of format ITEM=val
            if ( len(fields) == 2 and len(fields[1])>=1 ):
                # Handle the various answers
                if fields[0] == 'PWR': # Power status update
                    self.UpdatePwrStatus(fields[1])
                elif fields[0] == 'ERR': # Error status update
                    self.UpdateErrorStatus(fields[1])
                elif fields[0] == 'LAMP': # Lamp counter update 1
                    self.UpdateLampCounter(fields[1])
                else:
                    Domoticz.Log("Unknown answer received : " + str(m))
            elif ( i == nb_msgs-1 ): # The last message is incomplete
                self.Received = m # Store the partial message
        return


    def onCommand(self, Unit, Command, Level, Hue):
        # Called when switch is actuated in Domoticz
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        if self.SerialConn is None:
            Domoticz.Log("Command requested but serial port not connected")
        elif Unit == 1 :
            if Command=="Off" :
                self.SerialConn.Send("PWR OFF\r")
                Domoticz.Status("Switching OFF")
            elif Command=="On" :
                self.SerialConn.Send("PWR ON\r")
                Domoticz.Status("Switching ON")
        return


    def onDisconnect(self, Connection):
        for Device in Devices:
            Devices[Device].Update(nValue=Devices[Device].nValue, sValue=Devices[Device].sValue, TimedOut=1)
            Domoticz.Status("Connection '"+Connection.Name+"' disconnected.")
        return


    def onHeartbeat(self):
        # Called every x seconds (see configuration)
        # Poll the projector
        if self.SerialConn is None:
            Domoticz.Error("Serial port not connected")
        else:
            # Prepare the list of Requests
            if not self.RequestsList:
                if self.ProjectorOn: #Projector is ON, use the RequestsListOn
                    self.RequestsList = self.RequestsListOn.copy()
                else:
                    self.RequestsList = self.RequestsListOff.copy()
            Domoticz.Log("list = " + ";".join(self.RequestsList))
            # Send Request
            msg = self.Requests[self.RequestsList.pop()]
            self.SerialConn.Send(msg)
            Domoticz.Log("Sent : "+ msg)


    def UpdatePwrStatus(self,PwrValue):
        Dev = Devices[1] # Projector domoticz Switch device
        if PwrValue == "00": # Off
            nValue = 0
            self.ProjectorOn = False
        elif PwrValue == "01": # On
            nValue = 1
            self.ProjectorOn = True
        elif PwrValue == "02": # Warming Up
            nValue = 1
            self.ProjectorOn = True
        elif PwrValue == "03": # Cooling Down
            nValue = 0
            self.ProjectorOn = False
        elif PwrValue == "05": # Abnormal shutdown
            nValue = 0
            self.ProjectorOn = False
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


    def UpdateLampCounter(self, LampHour):
        Dev = Devices[3] # Counter
        TimedOut = 0
        sValue=str(LampHour)
        if (Dev.sValue != sValue) or (Dev.TimedOut != TimedOut):
            Dev.Update(nValue=0, sValue=sValue, TimedOut=TimedOut)
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
