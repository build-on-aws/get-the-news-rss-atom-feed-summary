from machine import Pin, SPI
import framebuf
import utime
import time
import rp2

import network
import urequests as requests
from time import sleep
from picozero import pico_temp_sensor, pico_led
from micropython import const
import machine

import json


# Parameters to update

NEWS_URL = 'https://BUCKER-NAME.s3.REGION.amazonaws.com/news.json'
SSID = const('WIFI-NETWORK-NAME')
PASSWORD = const('WIFI-NETWORK-PASSWORD')


# Display specific libraries and code

WF_PARTIAL_2IN13_V3 = [
    0x0, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x80, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x40, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x14, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x0, 0x0, 0x0,
    0x22, 0x17, 0x41, 0x00, 0x32, 0x36,
]

WS_20_30_2IN13_V3 = [
    0x80, 0x4A, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x40, 0x4A, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x80, 0x4A, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x40, 0x4A, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0xF, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0xF, 0x0, 0x0, 0xF, 0x0, 0x0, 0x2,
    0xF, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x0, 0x0, 0x0,
    0x22, 0x17, 0x41, 0x0, 0x32, 0x36
]

EPD_WIDTH = const(122)
EPD_HEIGHT = const(250)

RST_PIN = const(12)
DC_PIN = const(8)
CS_PIN = const(9)
BUSY_PIN = const(13)


class EPD_2in13_V3_Portrait(framebuf.FrameBuffer):
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)

        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        if EPD_WIDTH % 8 == 0:
            self.width = EPD_WIDTH
        else:
            self.width = (EPD_WIDTH // 8) * 8 + 8
        self.height = EPD_HEIGHT

        self.full_lut = WF_PARTIAL_2IN13_V3
        self.partial_lut = WS_20_30_2IN13_V3

        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_HLSB)
        self.init()

    '''
    function :Change the pin state
    parameter:
        pin : pin
        value : state
    '''

    def digital_write(self, pin, value):
        pin.value(value)

    '''
    function : Read the pin state 
    parameter:
        pin : pin
    '''

    def digital_read(self, pin):
        return pin.value()

    '''
    function : The time delay function
    parameter:
        delaytime : ms
    '''

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    '''
    function : Write data to SPI
    parameter:
        data : data
    '''

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    '''
    function :Hardware reset
    parameter:
    '''

    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)

    '''
    function :send command
    parameter:
     command : Command register
    '''

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    '''
    function :send data
    parameter:
     data : Write data
    '''

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)

    '''
    function :Wait until the busy_pin goes LOW
    parameter:
    '''

    def ReadBusy(self):
        print('busy')
        self.delay_ms(10)
        while (self.digital_read(self.busy_pin) == 1):      # 0: idle, 1: busy
            self.delay_ms(10)
        print('busy release')

    '''
    function : Turn On Display
    parameter:
    '''

    def TurnOnDisplay(self):
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xC7)
        self.send_command(0x20)  # Activate Display Update Sequence
        self.ReadBusy()

    '''
    function : Turn On Display Part
    parameter:
    '''

    def TurnOnDisplayPart(self):
        self.send_command(0x22)  # Display Update Control
        self.send_data(0x0F)     # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20)  # Activate Display Update Sequence
        self.ReadBusy()

    '''
    function : Set lut
    parameter:
        lut : lut data
    '''

    def LUT(self, lut):
        self.send_command(0x32)
        self.send_data1(lut[0:153])
        self.ReadBusy()

    '''
    function : Send lut data and configuration
    parameter:
        lut : lut data 
    '''

    def LUT_by_host(self, lut):
        self.LUT(lut)             # lut
        self.send_command(0x3F)
        self.send_data(lut[153])
        self.send_command(0x03)   # gate voltage
        self.send_data(lut[154])
        self.send_command(0x04)   # source voltage
        self.send_data(lut[155])  # VSH
        self.send_data(lut[156])  # VSH2
        self.send_data(lut[157])  # VSL
        self.send_command(0x2C)   # VCOM
        self.send_data(lut[158])

    '''
    function : Setting the display window
    parameter:
        Xstart : X-axis starting position
        Ystart : Y-axis starting position
        Xend : End position of X-axis
        Yend : End position of Y-axis
    '''

    def SetWindows(self, Xstart, Ystart, Xend, Yend):
        self.send_command(0x44)  # SET_RAM_X_ADDRESS_START_END_POSITION
        self.send_data((Xstart >> 3) & 0xFF)
        self.send_data((Xend >> 3) & 0xFF)

        self.send_command(0x45)  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)
        self.send_data(Yend & 0xFF)
        self.send_data((Yend >> 8) & 0xFF)

    '''
    function : Set Cursor
    parameter:
        Xstart : X-axis starting position
        Ystart : Y-axis starting position
    '''

    def SetCursor(self, Xstart, Ystart):
        self.send_command(0x4E)  # SET_RAM_X_ADDRESS_COUNTER
        self.send_data(Xstart & 0xFF)

        self.send_command(0x4F)  # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)

    '''
    function : Initialize the e-Paper register
    parameter:
    '''

    def init(self):
        print('init')
        self.reset()
        self.delay_ms(100)

        self.ReadBusy()
        self.send_command(0x12)  # SWRESET
        self.ReadBusy()

        self.send_command(0x01)  # Driver output control
        self.send_data(0xf9)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x03)

        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)

        self.send_command(0x3C)  # BorderWaveform
        self.send_data(0x05)

        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x80)

        self.send_command(0x18)  # Read built-in temperature sensor
        self.send_data(0x80)

        self.ReadBusy()
        self.LUT_by_host(self.partial_lut)

    '''
    function : Clear screen
    parameter:
    '''

    def Clear(self):
        self.send_command(0x24)
        self.send_data1([0xff] * self.height * int(self.width / 8))

        self.TurnOnDisplay()

    '''
    function : Sends the image buffer in RAM to e-Paper and displays
    parameter:
        image : Image data
    '''

    def display(self, image):
        self.send_command(0x24)
        self.send_data1(image)

        self.TurnOnDisplay()

    '''
    function : Refresh a base image
    parameter:
        image : Image data
    '''

    def Display_Base(self, image):
        self.send_command(0x24)
        self.send_data1(image)

        self.send_command(0x26)
        self.send_data1(image)

        self.TurnOnDisplay()

    '''
    function : Sends the image buffer in RAM to e-Paper and partial refresh
    parameter:
        image : Image data
    '''

    def display_Partial(self, image):
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(1)
        self.digital_write(self.reset_pin, 1)

        self.LUT_by_host(self.full_lut)

        self.send_command(0x37)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x40)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x3C)
        self.send_data(0x80)

        self.send_command(0x22)
        self.send_data(0xC0)
        self.send_command(0x20)
        self.ReadBusy()

        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)

        self.send_command(0x24)
        self.send_data1(image)

        self.TurnOnDisplayPart()

    '''
    function : Enter sleep mode
    parameter:
    '''

    def sleep(self):
        self.send_command(0x10)  # enter deep sleep
        self.send_data(0x01)
        self.delay_ms(100)


class EPD_2in13_V3_Landscape(framebuf.FrameBuffer):
    def __init__(self):
        self.reset_pin = Pin(RST_PIN, Pin.OUT)

        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        if EPD_WIDTH % 8 == 0:
            self.width = EPD_WIDTH
        else:
            self.width = (EPD_WIDTH // 8) * 8 + 8

        self.height = EPD_HEIGHT

        self.full_lut = WF_PARTIAL_2IN13_V3
        self.partial_lut = WS_20_30_2IN13_V3

        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.height, self.width, framebuf.MONO_VLSB)
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(20)

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        print('busy')
        self.delay_ms(10)
        while (self.digital_read(self.busy_pin) == 1):      # 0: idle, 1: busy
            self.delay_ms(10)
        print('busy release')

    def TurnOnDisplay(self):
        self.send_command(0x22)  # Display Update Control
        self.send_data(0xC7)
        self.send_command(0x20)  # Activate Display Update Sequence
        self.ReadBusy()

    def TurnOnDisplayPart(self):
        self.send_command(0x22)  # Display Update Control
        self.send_data(0x0F)     # fast:0x0c, quality:0x0f, 0xcf
        self.send_command(0x20)  # Activate Display Update Sequence
        self.ReadBusy()

    def LUT(self, lut):
        self.send_command(0x32)
        self.send_data1(lut[0:153])
        self.ReadBusy()

    def LUT_by_host(self, lut):
        self.LUT(lut)             # lut
        self.send_command(0x3F)
        self.send_data(lut[153])
        self.send_command(0x03)   # gate voltage
        self.send_data(lut[154])
        self.send_command(0x04)   # source voltage
        self.send_data(lut[155])  # VSH
        self.send_data(lut[156])  # VSH2
        self.send_data(lut[157])  # VSL
        self.send_command(0x2C)   # VCOM
        self.send_data(lut[158])

    def SetWindows(self, Xstart, Ystart, Xend, Yend):
        self.send_command(0x44)  # SET_RAM_X_ADDRESS_START_END_POSITION
        self.send_data((Xstart >> 3) & 0xFF)
        self.send_data((Xend >> 3) & 0xFF)

        self.send_command(0x45)  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)
        self.send_data(Yend & 0xFF)
        self.send_data((Yend >> 8) & 0xFF)

    def SetCursor(self, Xstart, Ystart):
        self.send_command(0x4E)  # SET_RAM_X_ADDRESS_COUNTER
        self.send_data(Xstart & 0xFF)

        self.send_command(0x4F)  # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(Ystart & 0xFF)
        self.send_data((Ystart >> 8) & 0xFF)

    def init(self):
        print('init')
        self.reset()
        self.delay_ms(100)

        self.ReadBusy()
        self.send_command(0x12)  # SWRESET
        self.ReadBusy()

        self.send_command(0x01)  # Driver output control
        self.send_data(0xf9)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x07)

        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)

        self.send_command(0x3C)  # BorderWaveform
        self.send_data(0x05)

        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x80)

        self.send_command(0x18)  # Read built-in temperature sensor
        self.send_data(0x80)

        self.ReadBusy()
        self.LUT_by_host(self.partial_lut)

    def Clear(self):
        self.send_command(0x24)
        self.send_data1([0xff] * self.height * int(self.width / 8))

        self.TurnOnDisplay()

    def display(self, image):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])

        self.TurnOnDisplay()

    def Display_Base(self, image):
        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])

        self.send_command(0x26)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])

        self.TurnOnDisplay()

    def display_Partial(self, image):
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(1)
        self.digital_write(self.reset_pin, 1)

        self.LUT_by_host(self.full_lut)

        self.send_command(0x37)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x40)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x3C)
        self.send_data(0x80)

        self.send_command(0x22)
        self.send_data(0xC0)
        self.send_command(0x20)
        self.ReadBusy()

        self.SetWindows(0, 0, self.width-1, self.height-1)
        self.SetCursor(0, 0)

        self.send_command(0x24)
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])

        self.TurnOnDisplayPart()

    def sleep(self):
        self.send_command(0x10)  # enter deep sleep
        self.send_data(0x01)
        self.delay_ms(100)


# Connect the Raspberri Pi Pico W to a Wi-Fi network

def connect(ssid, password):
    # Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    # print(wlan.ifconfig())
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip


# Download the news into a Python dictionary

def get_news():
    print('get_news')
    try:
        ip = connect(SSID, PASSWORD)
        res = requests.get(NEWS_URL)
        news = json.loads(res.text)
        return news
    except (KeyboardInterrupt, ValueError):
        machine.reset()


# Display size (landscape mode)

MAX_WIDTH = const(32)
MAX_HEIGHT = const(12)


# Format text for the display size

def wrap_text(text):
    lines = []
    for line in text.splitlines():
        wrapped_text = ''
        for word in line.split():
            if len(word) + len(wrapped_text) >= MAX_WIDTH - 1:
                if len(lines) < MAX_HEIGHT:
                    lines.append(wrapped_text)
                wrapped_text = ''
            if len(wrapped_text) > 0:
                wrapped_text += ' '
            wrapped_text += word
        lines.append(wrapped_text)
    lines = [' ' * int((MAX_WIDTH - len(l))/2) + l for l in lines]
    for _ in range((MAX_HEIGHT - len(lines) - 1)/2):
        lines.insert(0, '')
    return lines


# Show the news on the display

def display_news(news):
    print('display_news')
    print(news)
    title = news['title']
    news_list = [title] + [e['summary'] for e in news['entries']]
    for n in news_list:
        epd.Clear()
        epd.fill(0xff)
        epd.display_Partial(epd.buffer)
        lines = wrap_text(n)
        y = 0
        for line in lines:
            y += 10
            epd.text(line, 0, y, 0x00)
        epd.display_Partial(epd.buffer)
        for _ in range(10):
            if rp2.bootsel_button() != 0: # Exit if the use presses the button on the Raspberry Pi Pico
                return False
            time.sleep(1)
    return True


# Main

if __name__ == '__main__':

    epd = EPD_2in13_V3_Landscape()
    epd.Clear()
    epd.fill(0xff)

    while True:
        news = get_news()
        if display_news(news) == False:
            break

    epd.init()
    epd.Clear()
    epd.delay_ms(2000)
    epd.sleep()
