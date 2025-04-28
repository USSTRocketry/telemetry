import time
import board
import digitalio
import adafruit_rfm9x

class RFM95Radio():
    def __init__(self, cs_pin, reset_pin, spi=board.SPI(), frequency=915.0, baudrate=4000000, node=1):
        self.cs = digitalio.DigitalInOut(cs_pin)
        self.reset = digitalio.DigitalInOut(reset_pin)
        self.radio = adafruit_rfm9x.RFM9x(spi, self.cs, self.reset, frequency, baudrate)
        self.radio.get_sync_word(0x12)  # Set sync word to 0x12
        self.radio.enable_crc = True
        self.radio.node = node
        self.radio.destination = node + 1
        self.radio.tx_power = 23  # Set transmit power to maximum (23 dBm)

    def send(self, data):
        self.radio.send(data)
        print(f"Sent: {data}")
    
    def receive(self) -> str:
        packet = self.radio.receive(timeout=1.0)  # Wait for 1 second for a packet
        if packet is not None:
            recv = str(packet, 'ascii')
            print(f"Received: {recv}")
            return recv
        else:
            print("No packet received")
            return None
    
    def rssi(self):
        rssi = self.radio.last_rssi
        return rssi

    def snr(self):
        snr = self.radio.last_snr
        return snr
    
    def set_node(self, node):
        self.radio.node = node

    def set_destination(self, destination):
        self.radio.destination = destination
    
    def set_tx_power(self, power):
        self.radio.tx_power = power

    def set_frequency(self, frequency):
        self.radio.frequency = frequency

    def reset(self):
        self.radio.reset()
