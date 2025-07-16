import queue
import threading
import serial
import serial.tools.list_ports as port_list
from time import sleep



class SerialMgr:

    comPorts = {}
    ignorePorts = ['COM5']
    ser = None
    keepRunning = True

    def __init__(self):
         # Create a thread-safe queue
        self.read_queue = queue.Queue()
        self.write_queue = queue.Queue()
        self._start_serial()
        
    def ConnectSerial(self):
        self.ports = list(port_list.comports())
        for p in self.ports:
            if p.device not in self.ignorePorts:
                self.comPorts[p.device] = p
                print(p.device)

        # Initialize the serial port
        for p in self.comPorts:
            try:
                self.ser = serial.Serial(p, 115200, timeout=1)  # Adjust COM port and baudrate as needed
                break
            except serial.SerialException:
                print(f"Unable to open: {p}")


    def IsConnected(self) -> bool:
        if self.ser and self.ser.is_open:
            return True
        return False
        # TODO: add logic to check we are connected to a transponder, not just anything


    def _read_from_serial(self):
        """Reads data from the serial port and puts it into the queue."""
        while self.keepRunning:
            if not self.IsConnected():
                sleep(1)
            else:
                try:
                    if self.ser.in_waiting > 0:
                        data = self.ser.readline().decode('utf-8').strip()
                        self.read_queue.put(data)  # Add data to the queue
                        #print(f"Received: {data}")
                    sleep(0.01)
                except Exception as e:
                    print(e)
                    self.CloseSerial()

    def _serial_writer(self):
        """Thread function to write data from the queue to the serial port."""
        while self.keepRunning:
            if not self.IsConnected():
                sleep(1)
            else:
                try:
                    # Get data from the queue (blocks until data is available)
                    data = self.write_queue.get()
                    if data is None: # Exit signal
                        break
                    self.ser.write(data)
                    sleep(0.01) # this seems to prevent serial writes from stepping on each other
                except Exception as e:
                    print(f"Error writing to serial {e}")

    def MessageReady(self) -> bool:
        if not self.ser:
            return False
        return not self.read_queue.empty()

    def GetMessage(self) -> str:
        if not self.ser:
            return ""
        data = self.read_queue.get()
        self.read_queue.task_done()
        return data

    def _start_serial(self):
        # Create and start threads
        reader_thread = threading.Thread(target=self._read_from_serial, daemon=True)
        writer_thread = threading.Thread(target=self._serial_writer, daemon=True)

        reader_thread.start()
        writer_thread.start()

    def WriteSerial(self, message):
        if not self.ser:
            return
        msg = (message + "\r\n").encode('utf-8')
        self.write_queue.put(msg)

    def CloseSerial(self):
        if self.ser:
            self.ser.close()
        keepRunning = False

# Keep the main thread alive
#try:
#    while True:
#        pass
#except KeyboardInterrupt:
#    print("Exiting...")
#    ser.close()