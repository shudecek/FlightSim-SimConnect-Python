import logging, logging.handlers
from simconnect_mobiflight import SimConnectMobiFlight
from mobiflight_variable_requests import MobiFlightVariableRequests
from time import sleep
import FlightSim_Xpndr
#from SimConnect import SimConnect, AircraftEvents

def setupLogging(logFileName):
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    fileHandler = logging.handlers.RotatingFileHandler(logFileName, maxBytes=500000, backupCount=7)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

# MAIN
setupLogging("SimConnectMobiFlight.log")
sm = SimConnectMobiFlight()
vr = MobiFlightVariableRequests(sm)
vr.clear_sim_variables()

indicated_altitude = vr.get("(A:INDICATED ALTITUDE:1,feet)") # needed for FL display
#vr._list_sim_variables()
#sc = SimConnect()
#ae = AircraftEvents(sc)

#fs = FlightSim_Xpndr.FlightSim_Xpndr()
#fs.SetMode(4);

vr.set("4.0 (>A:TRANSPONDER STATE:1,number)") # works
bcdCode = str((4<<12) + (5<<8) + (6<<4) + 7)
vr.set(bcdCode + " (>A:TRANSPONDER CODE:1,number)") # BCD16, slso XPNDR_SET

# need to figure out how to trigger ident, simconnect event
# XPNDR_IDENT_TOGGLE
vr.set('(>K:XPNDR_IDENT_TOGGLE)')

# sample using AircraftEvents
#bcdNum = (4<<12) + (5<<8) + (6<<4) + 7
#xpdr_set = ae.find("XPNDR_SET")
#xpdr_set(bcdNum)

while True:
    mode = fs.GetMode()
    sleep(1)


while True:
    #alt_ground = vr.get("(A:GROUND ALTITUDE,Meters)")
    #alt_plane = vr.get("(A:PLANE ALTITUDE,Feet)")
    # FlyByWire A320
    #ap1 = vr.get("(L:A32NX_AUTOPILOT_1_ACTIVE)")
    #hdg = vr.get("(L:A32NX_AUTOPILOT_HEADING_SELECTED)")
    #mode = vr.get("(L:A32NX_FMA_LATERAL_MODE)")
    #prop_prm = vr.get("(A:PROP RPM:1,rpm)")

    indicated_altitude = vr.get("(A:INDICATED ALTITUDE:1,feet)") # needed for FL display
    transponder_available = vr.get("(A:TRANSPONDER AVAILABLE:1,bool)") #
    transponder_code = vr.get("(A:TRANSPONDER CODE:1,number)") # read and write
    transponder_ident = vr.get("(A:TRANSPONDER IDENT:1,bool)") # 1.0 = ident
    transponder_state = vr.get("(A:TRANSPONDER STATE:1,number)") # 0.0 = off, 1.0 = standby, 2.0 = test, 3.0 = on, 4.0=alt
    #mode = fs.GetMode()


    sleep(1)