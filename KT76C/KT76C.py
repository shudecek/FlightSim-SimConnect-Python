import logging, logging.handlers
from time import sleep, time
from FlightSim_Xpndr import *
from serialmgr import *
import queue
import math
from enum import Enum
import configparser

CONFIG_FILENAME = 'config.ini'
CONFIG_SETTINGS = 'Settings'
CONFIG_VFRCODE = 'vfrCode'

class ButtonState(Enum):
    Released = 0
    Pressed = 1
    Holding = 2
    Undefined = 3

mode = 0
alt = -9999
code = 5000
brightness = 10
lastNonVfrCode = 5000
ident = False
knownTransponder = False
codeEntryPending = False
lastEntry = time()
lastSimRead = time()
lastSimConnectionCheck = time()
lastKeyPressed = ''
lastVfrPressed = time()
identButtonState = ButtonState.Undefined
vfrButtonState = ButtonState.Undefined

config = configparser.ConfigParser()
config.read(CONFIG_FILENAME)
vfrCode = int(config[CONFIG_SETTINGS][CONFIG_VFRCODE])

def decreaseBrightness():
    global brightness
    brightness -= 1
    if brightness <= 1:
        brightness = 1
    cmd = f"26,0,0,{brightness};"
    print(cmd)
    sm.WriteSerial(cmd)
    brightnessChanged = True
    

def increaseBrightness():
    global brightness
    brightness += 1
    if brightness >= 15:
        brightness = 15
    cmd = f"26,0,0,{brightness};"
    print(cmd)
    sm.WriteSerial(cmd)
     
def defaultBrightness():
    global brightness
    brightness = 10
    cmd = f"26,0,0,{brightness};"
    print(cmd)
    sm.WriteSerial(cmd)



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

number_entry = []

def pushNumberKey(key):
    if len(number_entry) >= 4:
        number_entry.clear()
    number_entry.append(key)
    codeEntryFinish()

def clearNumberKey():
    if len(number_entry) > 0:
        del number_entry[-1]
    codeEntryFinish()

def codeEntryFinish():
    global codeEntryPending
    global lastEntry
    if codeEntryPending == False:
        display(' ',0,16)
    codeEntryPending = True
    lastEntry = time()


def entryAsString(numEntry) -> str:
    s = ''.join(map(str, numEntry)) # concat items to string
    padded = s.ljust(4,'-')
    print(s)
    return padded

def displayNumberEntry():
     s = entryAsString(number_entry)
     display(s, 16, 15)

def displayCode(c):
    s = str(int(c)).rjust(4, '0')
    display(s, 0, 15)

def updateDisplayMode():
    if mode == 0:
        display('        ', 0, 255)
    elif mode == 1:
        display('5b4 ', 0, 240)
        displayCode(code)
    elif mode == 2:
        display('-888', 0, 240)
        displayCode('8888')
    elif mode == 3:
        display(' on ', 0, 240)
        displayCode(code)
    elif mode == 4:
        if alt < -1000 or alt > 62700:  # this is the range that the KT-76C supports in the manual
             display(f'--- ', 0, 240)
        elif alt >= 0:
            a = str(round((max(0,alt))*0.01)).rjust(3, '0')
            display(f'{a} ', 16, 240)
        elif alt < 0:
            a = str(round((0-alt)*0.01)).rjust(2, '0')
            display(f'-{a} ', 16, 240)
        displayCode(code)

def timeBasedIndicatorOn(pct):
    dec, _ = math.modf(time())
    if dec <= pct:
        if timeBasedIndicatorOn.isOn == False:
            display(' ',16,16)
        timeBasedIndicatorOn.isOn = True
    else:
        if timeBasedIndicatorOn.isOn == True:
            display(' ',0,16)
        timeBasedIndicatorOn.isOn = False
timeBasedIndicatorOn.isOn = False


def updateReplyIndicator():
    if (mode == 3 or mode == 4) and codeEntryPending == False:
        timeBasedIndicatorOn(0.1)

def display(digits,point,mask):
    data = f"1,0,0,{digits},{point},{mask};"
    sm.WriteSerial(data)

def pushCode(code:int):
    number_entry.clear()
    s = str(int(code)).rjust(4, '0')
    for c in s:
        pushNumberKey(c)
    displayNumberEntry()


def updateCodeFromPending():
    global code
    global codeEntryPending
    global lastNonVfrCode
    codeEntryPending = False
    if len(number_entry) != 4:
        # code entered is not complete, restore current code to display
        displayCode(code)
    else:
        # code entered is complete
        code = int("".join(map(str, number_entry)))
        if code != vfrCode:
            lastNonVfrCode = code
        print(f'updating code to {code}')
        fs.CodeIntSet(code)
        displayCode(code)
        display(' ',16,16)
        sleep(0.25)
        display(' ',0,16)
    number_entry.clear()

def changeMode(newMode):
    global mode
    global codeEntryPending

    codeEntryPending = False
    number_entry.clear()

    fs.ModeSet(newMode)
    mode = newMode
    updateDisplayMode()

def saveConfig():
    with open(CONFIG_FILENAME, 'w') as configfile:
        config.write(configfile)


# MAIN
setupLogging("KT76C.log")
sm = SerialMgr()
fs = FlightSim_Xpndr()

def isEntryMode() -> bool:
    return mode in [4,3,1] # number entry allowed in modes STDBY,ON,ALT


try:
    while True:
        if not sm.IsConnected():
            sm.ConnectSerial()
            sleep(0.2)

        if sm.IsConnected():
            while sm.MessageReady():
                msg = sm.GetMessage()
                print(f"Processing: {msg}")
                if knownTransponder == False:
                    if msg == "17,OK;":      # ConfigActivated
                        sm.WriteSerial("18,1;")
                        sm.WriteSerial("9;") # GetInfo
                    elif msg.startswith("10,"): #Info
                        knownTransponder = True
                        sm.WriteSerial("18,0;") # SetPowerSavingMode = false
                        sm.WriteSerial("12;") # GetConfig
                        sm.WriteSerial("23;") # Retrigger
                        #sm.WriteSerial("5,0,0;") # Status
                        defaultBrightness()
                else:
                    clean_msg = msg[:-1] if msg.endswith(';') else msg 
                    msg_items = clean_msg.split(',')
                    key = ''
                    if len(msg_items) == 3:
                        key = msg_items[1]
                        if msg_items[0] == '7' and msg_items[2] == '0': # key pressed
                            if key in ('0','1','2','3','4','5','6','7'):
                                lastKeyPressed = key
                        if msg_items[0] == '7' and msg_items[2] == '1': # key released
                            if key in ('0','1','2','3','4','5','6','7') and key != lastKeyPressed:
                                continue # filter release without a press right before

                        if key in ('0','1','2','3','4','5','6','7')  and msg_items[2] == '1' and msg_items[0] == '7':  # button released
                            if isEntryMode():
                                pushNumberKey(key)
                                displayNumberEntry()
                            elif mode == 2: # tst mode
                                match key:
                                    case '0':
                                        decreaseBrightness()
                                    case '4':
                                        defaultBrightness()
                                    case '7':
                                        increaseBrightness()
                        else:
                            match msg:
                                case "7,CLR,1;":    # CLR
                                    if isEntryMode():
                                        clearNumberKey()
                                        displayNumberEntry()
                                case "7,VFR,0;":    # VFR (press)
                                    if mode in (3,4):
                                        lastVfrPressed = time()
                                        vfrButtonState = ButtonState.Pressed
                                case "7,VFR,1;":    # VFR (release)
                                    if mode in (3,4):
                                        vfrButtonState = ButtonState.Released
                                        if code != vfrCode:
                                            pushCode(vfrCode)
                                    elif mode == 1 and identButtonState == ButtonState.Pressed:
                                        updateCodeFromPending()
                                        vfrCode = code
                                        config[CONFIG_SETTINGS][CONFIG_VFRCODE] = str(vfrCode)
                                        saveConfig()
                                case "7,IDT,0;":    # ident (press)
                                    identButtonState = ButtonState.Pressed
                                case "7,IDT,1;":    # ident (release)
                                    if identButtonState != ButtonState.Pressed:
                                        break
                                    identButtonState = ButtonState.Released
                                    if mode not in (3, 4):
                                        break
                                    updateCodeFromPending()
                                    fs.IdentToggle()
                                case "7,RS_ALT,0;": # alt mode
                                    changeMode(4)
                                case "7,RS_ON,0;":  # on mode
                                    changeMode(3)
                                case "7,RS_OFF,0;": # off mode
                                    changeMode(0)
                                case "7,RS_TST,0;": # test mode
                                    changeMode(2)
                                case "7,RS_SBY,0;": # standby mode
                                    changeMode(1)
            if codeEntryPending and time() > lastEntry + 3.5:
                updateCodeFromPending()
            if ident == False:
                updateReplyIndicator()
            if vfrButtonState == ButtonState.Pressed and time() > lastVfrPressed + 2.0 and code == vfrCode:
                vfrButtonState = ButtonState.Holding
                pushCode(lastNonVfrCode)
        if fs.IsConnected():
            if time() > lastSimRead + 1.0:
                lastSimRead = time()
                alt = fs.AltitudeGet()
                code = fs.CodeGet()
                ident = fs.IdentGet()
                if codeEntryPending == False:
                    updateDisplayMode()
            
            # update local display
            if ident == True:
                timeBasedIndicatorOn(0.9)

        if not fs.IsInitialized() and not fs.IsConnected() and time() > lastSimConnectionCheck + 5.0:
            lastSimConnectionCheck = time()
            if (fs.Connect()):
                fs.Initialize()

        sleep(0.01)
except KeyboardInterrupt:
    print("Exiting...")
    sm.CloseSerial()










try:
    while True:
        mode = fs.ModeGet()
        alt = fs.AltitudeGet()
        code = fs.CodeGet()
        ident = fs.IdentGet()
        sleep(1)
        while sm.MessageReady():
            msg = sm.GetMessage()
            print(f"Processing: {msg}")
            
except KeyboardInterrupt:
    print("Exiting...")
    sm.CloseSerial()



