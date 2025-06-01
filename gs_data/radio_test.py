from .radio import RFM95Radio
import board
import time

# default SPI bus (SPI0) 
#   SCLK = GPIO11 (Pin 23)
#   MOSI = GPIO10 (Pin 19)
#   MISO = GPIO9 (Pin 21)
spi = board.SPI() 
radio = RFM95Radio(spi=spi, cs_pin=board.D17, reset_pin=board.D27, frequency=915.0, baudrate=4000000, node=1)

def recieve_test():
    print("Starting receive test...")
    while True:
        packet = radio.receive()
        if packet:
            print(f"Received packet: {packet}")
        else:
            print("No packet received, retrying...")
        time.sleep(1)  # Wait for a second before the next attempt
if __name__ == "__main__":
    recieve_test()