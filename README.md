# Code to implement Captain Bob's KT6C Transponder logic in Python
### based on: 

### MSFS Python SimConnect Extension:
https://github.com/Koseng/MSFSPythonSimConnectMobiFlightExtension

### Captain Bob's Transponder:
https://www.youtube.com/watch?v=-2wvzZ1n_w0&t=1s

### Feature Demo
https://youtu.be/5hL7WlavQHw

### KT6C Manual:
https://vac.flights/index_htm_files/KT-76C_IM.pdf

### Demo
https://www.youtube.com/watch?v=Q1BpVzeiVFY

### Captain Bob's Tranponder PCB
https://captainbobsim.com/product/kt-76c-like-transponder-pcb/

This connects to the MobiFlight WASM module and the Captain Bob's KT76C with serial and implements the logic in Python.  Basically do everything he says, but run this Python script instead of MobiFlight



1. install MobiFlight WASM module (you can use MobiFlight for this or do it manually)
2. install Python depends:
    - pyserial     3.5
    - SimConnect   0.4.26
3. run it:
    - source\repos\FlightSim\KT76C> python KT76C.py



## Features
I tried to implement everything in the manual, given the limitations of the 8 digit display

- you can change the brightness, just like in the manual
- you can set the VRF code, just like in the manual.  (this is persisted to config.ini file for next startup)


Tested using FS2024 using Carenado PA28 181 Archer II


### Issues i've noticed
 - pressing Ident is supposed to toggle ident, ie turn of off the second time.  it appears to stay on, not sure if this is an issue with FS or my aircraft
 - turning off power save doesn't appear to work, the display turns off after a while