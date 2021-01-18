import pyaudio
import numpy as np
import serial
import serial.tools.list_ports
import rumps
import threading

PERIOD = 20
CHUNK = 2**10
RATE = 44100
LENGTH = 2**3
AMPLIFIER = 4
IDLE_COUNT_MAX = 200

p = pyaudio.PyAudio()

def get_port_devices() :
    devices = []
    ports = serial.tools.list_ports.comports()

    for port, desc, hwid in sorted(ports):
        devices.append(port)

    return devices

def get_audio_devices() :
    devices = {}
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')

    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            # print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
            devices[p.get_device_info_by_host_api_device_index(0, i).get('name')] = i

    return devices

class AudioLedApp(object) :
    def __init__(self) :
        self.port_devices = get_port_devices()
        self.audio_devices = get_audio_devices()

        self.port_device = self.port_devices[0]
        self.audio_device = list(self.audio_devices.values())[0]

        self.restart_trigger = False

        self.t = threading.Thread(target = self.render_led, args = (self.port_device, self.audio_device))
        
        self.app = rumps.App("AudioLed", icon = "icon.icns")
        self.set_up_menu()

    def set_up_menu(self) :
        port_devices_items = []
        audio_devices_items = []
        
        for port_device in self.port_devices :
            port_devices_items.append(rumps.MenuItem(port_device, callback = lambda sender: self.set_thread_port(sender)))

        for audio_device in list(self.audio_devices.keys()) :
            audio_devices_items.append(rumps.MenuItem(audio_device, callback = lambda sender: self.set_thread_audio(sender)))

        self.app.menu = [
            {'Port Devices' : port_devices_items},
            {'Audio Devices' : audio_devices_items},
            None,
        ]

    def run(self) :
        self.app.run()

    def set_thread_port(self, sender) :
        while self.t.is_alive() :
            self.restart_trigger = True

        self.restart_trigger = False
        device = sender.title
        print(device)
        self.port_device = device
        self.t = threading.Thread(target = self.render_led, args = (self.port_device, self.audio_device), daemon = True)
        self.t.start()

    def set_thread_audio(self, sender) :
        while self.t.is_alive() :
            self.restart_trigger = True

        self.restart_trigger = False
        device = sender.title
        print(device)
        print(self.audio_devices[device])
        self.audio_device = self.audio_devices[device]
        self.t = threading.Thread(target = self.render_led, args = (self.port_device, self.audio_device), daemon = True)
        self.t.start()

    def render_led(self, port_device, audio_device) :
        brt = np.zeros(LENGTH)
        index = 0
        idle_count = 0
        idle_status = False
        arduino = serial.Serial(port_device, 9600)

        try :
            stream = p.open(format = pyaudio.paInt16, channels = 2, rate = RATE, input = True, frames_per_buffer = CHUNK, input_device_index = audio_device)

        except :
            print("Error occured!")

        while not self.restart_trigger :
            data = np.fromstring(stream.read(CHUNK), dtype = np.int16)
            brt[index] = np.clip(int(AMPLIFIER * 256 * np.average(np.abs(data)) / 32757), 0, 255)

            _brt = int(np.mean(brt))

            if _brt == 0 :
                if idle_status :
                    continue

                elif idle_count == IDLE_COUNT_MAX :
                    idle_status = True
                    print("Now triggered to idle status")
                    continue

                else :
                    idle_count += 1

            else :
                idle_count = 0

                if idle_status :
                    print("Now escaping idle status")

                idle_status = False

            arduino.write((str(_brt) + '\n').encode('utf-8'))

            # print('brt : ', _brt)

            index = (index + 1) % LENGTH

        stream.stop_stream()
        stream.close()
        # p.terminate()

if __name__ == '__main__' :
    app = AudioLedApp()
    app.run()
    p.terminate()