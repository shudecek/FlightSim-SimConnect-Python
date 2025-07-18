import logging, logging.handlers
from simconnect_mobiflight import SimConnectMobiFlight
from mobiflight_variable_requests import MobiFlightVariableRequests


class FlightSim_Xpndr:

    initialized = False

    def __init__(self):
        logging.info("FlightSim_Xpndr: __init__")
        self.sm = SimConnectMobiFlight(auto_connect=False)

    def Connect(self) -> bool:
        try:
            self.sm.connect()
            return True
        except Exception as e:
            print(e)
            return False
    
    def Initialize(self):
        self.vr = MobiFlightVariableRequests(self.sm)
        self.vr.clear_sim_variables()
        self.initialized = True

    def IsInitialized(self):
        return self.initialized

    def IsConnected(self):
        return self.sm.ok

    def IsAvailible(self) -> bool:
        if not self.IsConnected():
            return False;
        avail = self.vr.get("(A:TRANSPONDER AVAILABLE:1,bool)")
        return bool(avail)

    def ModeSet(self, code):
        if self.IsAvailible():
            self.vr.set(str(code) + " (>A:TRANSPONDER STATE:1,Enum)") 

    def ModeGet(self) -> int:
        if self.IsAvailible():
            transponder_state = self.vr.get("(A:TRANSPONDER STATE:1,Enum)") # 0.0 = off, 1.0 = standby, 2.0 = test, 3.0 = on, 4.0=alt
            return int(transponder_state)
        else:
            return 0
        
    def AltitudeGet(self) -> int:
        indicated_altitude = self.vr.get("(A:INDICATED ALTITUDE:1,feet)") # needed for FL display
        return int(indicated_altitude)

    def CodeGet(self) -> int:
        if self.IsAvailible():
            transponder_code = self.vr.get("(A:TRANSPONDER CODE:1,number)")
            return transponder_code
        else:
            return 0

    def AvionicsMasterSwitchGet(self) -> int:
        if self.IsAvailible():
            master_switch = self.vr.get("(A:AVIONICS MASTER SWITCH:1,number)") # 
            return int(master_switch)
        else:
            return 0

    def CodeSet(self, n3, n2, n1, n0):
        if self.IsAvailible():
            bcdCode = str((n3<<12) + (n2<<8) + (n1<<4) + n0)
            self.vr.set(bcdCode + " (>A:TRANSPONDER CODE:1,number)") # BCD16, slso XPNDR_SET

    def CodeIntSet(self, code):
        if self.IsAvailible():
            n0 = code % 10
            code = int(code * 0.1)
            n1 = code % 10
            code = int(code * 0.1)
            n2 = code % 10
            code = int(code * 0.1)
            n3 = code % 10
            self.CodeSet( n3, n2, n1, n0)

    def IdentGet(self) -> bool:
        if self.IsAvailible():
            ident = self.vr.get("(A:TRANSPONDER IDENT:1,bool)")
            return bool(ident)
        else:
            return False

    def IdentToggle(self):
        if self.IsAvailible():
            self.vr.set('(>K:XPNDR_IDENT_TOGGLE)')




