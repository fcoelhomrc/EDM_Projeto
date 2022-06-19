from machine import Pin, PWM, Timer
import time
import network, socket, urequests

def do_connect():
    '''
    Connects to local Wi-Fi
    '''
    essid = "NOS-D610" # "Galaxy A32 5G1A70"
    password = "fbe228d0bc19"  # "yfee4537"

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print(wlan.scan())
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(essid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

def parseQuerystring(url, qs):
    '''
    Parse a dictionary containing the query parameters
    and write them to the url
    '''
    query = f"?key={qs['key']}&src={qs['src']}&hl={qs['hl']}&r={qs['r']}&c={qs['c']}&f={qs['f']}"
    return url + query

def getColorName(RGB_values):
    R, G, B = tuple(RGB_values)
    if R > G and R > B:
        return "red"
    if G > R and G > B:
        return "green"
    if B > R and B > G:
        return "blue"
    if R < 20 and G < 20 and B < 20:
        return "black"
    if R > 230 and G > 230 and B > 230:
        return "white"
    else:
        return "unknown"


def convertTTS(name):
    print("Accessing VoiceRSS API...")
    url = "http://api.voicerss.org/"
    querystring = {
                   "key":"855df224b9e54663af317722f0a96eaf",
                   "src":name,
                   "hl":"en-us",
                   "r":"0",
                   "c":"mp3",
                   "f":"8khz_8bit_mono"
                   }
    parsed = parseQuerystring(url, querystring)
    api_response = urequests.request("GET", parsed)
    print("API response:", api_response.status_code)
    with open("test.mp3", mode="wb") as file:
        print("Writing .mp3 ...")
        file.write(api_response.content)
    print("Finished writing file")


with open("page.txt", mode="r") as file:
    html = file.read()
def updatePage(client, rgb_values):
    global html
    name = getColorName(rgb_values)
    # Generate TTS audio
    convertTTS(name)
    # Update HTML with new color
    index = html.find("rgb")
    new_rgb = f"rgb({rgb_values[0]:03d}, {rgb_values[1]:03d}, {rgb_values[2]:03d})"
    html = html[:index] + new_rgb + html[index+18:]
    # Send page HTML
    client.send('HTTP/1.0 200 OK content-type: text/html\r\n\r\n')
    client.send(html)
    # Send audio file
    client.send('HTTP/1.0 200 OK content-type: audio/mpeg')
    with open("test.mp3", "rb") as file:
        audio = file.read()
        client.send(audio)
    client.close()


# Selection pins
s3 = Pin(25, Pin.OUT)
s2 = Pin(27, Pin.OUT)
s1 = Pin(23, Pin.OUT)
s0 = Pin(26, Pin.OUT)

# Output frequency scaling
# 20% (s0 = 1, s1 = 0)
#  2% (s0 = 0, s1 = 1)
s0.value(0)
s1.value(1)

# Choose filter
def select_filter(mode):
    global s2, s3
    if mode == "red":
        s2.value(0)
        s3.value(0)
    elif mode == "green":
        s2.value(1)
        s3.value(1)
    elif mode == "blue":
        s2.value(0)
        s3.value(1)
    elif mode == "clear":
        s2.value(1)
        s3.value(0)
    else:
        print("Invalid mode")

# Sensor output
sensor_signal = Pin(19, Pin.IN)

def get_measurement(tag):
    global current_count, filters, filter_index, measure_interval
    global cache, dark_calib_cache, white_calib_cache
    global measure_timer, calib_timer
    global CALIBRATED, DARK_CALIBRATION, VERBOSE
    # Get measurement
    measurement = current_count/measure_interval # kHz
    if tag == measure_timer:

        if CALIBRATED:
            # Convert to RGB scale
            f0 = measurement
            fd = dark_calib_cache[filters[filter_index]]
            fw = white_calib_cache[filters[filter_index]]
            RGB = int(255*(f0 - fd)/(fw - fd))
            # Ensure that the value falls within RGB limits
            RGB = 255 if RGB > 255 else RGB
            RGB = 0 if RGB < 0 else RGB
            cache[filters[filter_index]] = RGB

        else:
            cache[filters[filter_index]] = measurement # Raw frequency measurement

        if filter_index == 3: # Finished measurement round, display results
            if VERBOSE:
                print(f"Results: {cache}")

    elif tag == calib_timer:
        print(f"Now writing value for {filters[filter_index]}...", end="\n")

        current_cache = dark_calib_cache if DARK_CALIBRATION else white_calib_cache # Decide which calibration stage we are at
        current_cache[filters[filter_index]] = measurement # Raw frequency measurement

    # Cycle through filters
    filter_index = (filter_index + 1)%4
    select_filter(filters[filter_index])
    # Reset counter
    current_count = 0

def increment(tag):
    global current_count
    current_count += 1

# Data storage
cache = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0} # Stores latest measurements
dark_calib_cache = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0} # Stores dark reference values
white_calib_cache = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0} # Stores white reference values

# Measurement constants
current_count = 0 # Counts number of full cycles during measure_interval
measure_interval = 200 # ms

# Sensor filter selection constants
filters = ["clear", "red", "green", "blue"]
filter_index = 0

# Timers for data acquisition
measure_timer = Timer(1) # Measurement cycle
calib_timer = Timer(2) # Calibration cycle

# Flags for event loop
CALIBRATED = False # Whether we have previously calibrated or not
DARK_CALIBRATION = False # Whether we are calibrating for dark reference or not (white)
LED_ACTIVE = False # Whether we have activated the LED or not
VERBOSE = True # Whether we print each measurement or not

# Input signal from sensor
# PWM with 50% duty and light intensity encoded in its frequency
sensor_signal.irq(trigger=Pin.IRQ_RISING, handler=increment) # Counts full cycles

def calibration():
    global measure_interval, filter_index, current_count
    global dark_calib_cache, white_calib_cache
    global calib_timer
    global CALIBRATED, DARK_CALIBRATION

    # Reset values
    dark_calib_cache = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0}
    white_calib_cache = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0}

    print("Beginning calibration for dark values...")
    current_count = 0 # Guarantees no left over counts
    initial_filter_index = filter_index
    filter_index = 0 # Start from the first filter option

    input("Place dark object and press Enter to continue...")

    DARK_CALIBRATION = True
    calib_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement)
    while True:
        for value in dark_calib_cache.values():
            if value < 0.01:
                break
        else:
            print("Interrupting calibration timer...")
            calib_timer.deinit()
            current_count = 0 # Guarantees no left over counts
            filter_index = 0 # Start from the first filter option
            break

    input("Place white object and press Enter to continue...")

    DARK_CALIBRATION = False
    calib_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement)
    while True:
        for value in white_calib_cache.values():
            if value < 0.01:
                break
        else:
            print("Interrupting calibration timer...")
            calib_timer.deinit()
            current_count = 0 # Guarantees no left over counts
            filter_index = initial_filter_index # Restore filter option in use before calibration
            break

    CALIBRATED = True
    print(f"Calibration results (dark): {dark_calib_cache}")
    print(f"Calibration results (white): {white_calib_cache}")

# Control pins for RGB LED
red_led = Pin(22, Pin.OUT) # Placeholder
green_led = Pin(21, Pin.OUT)
blue_led = Pin(18, Pin.OUT)

def loop(socket):
    global measure_interval
    global measure_timer
    global red_led, green_led, blue_led
    global LED_ACTIVE, VERBOSE



    measure_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement) # Begin measurement
    while True:
        command = input("Enter 'c' to begin calibration... \n" +
                        "Enter 'a' to activate LED with measured color... \n" +
                        "Enter 'v' to switch measurement display... \n")
        # Calibration
        if command == "c":
            print("Interrupt measurement timer...")
            measure_timer.deinit() # Stop normal measurement
            calibration() # Proceed with calibration
            print("Resume measurement timer...")
            measure_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement) # Resume measurement
        # Activate LED
        elif command == "a":
            if not CALIBRATED:
                print("Please, calibrate sensor before attempting to activate LED...")
                pass
            # Unpack duty values from cache
            RGB = [cache["red"], cache["green"], cache["blue"]]
            # Convert to duty
            convert_RGB2Duty = lambda x : int((1023/255)*x)
            DR, DG, DB = tuple(map(convert_RGB2Duty, RGB))
            print(f"Duty values: R ={DR}, G ={DG}, B ={DB}")
            # Control pins for RGB LED
            if not LED_ACTIVE:
                red_led = PWM(Pin(22), freq=500, duty=DR)
                green_led = PWM(Pin(21), freq=500, duty=DG)
                blue_led = PWM(Pin(18), freq=500, duty=DB)
            else:
                red_led.duty(DR)
                green_led.duty(DG)
                blue_led.duty(DB)
            ################################################################################
            while True:
                cl, addr = s.accept()
                print('Client connected from', addr)
                cl_file = cl.makefile('rwb', 0)
                while True:
                    line = cl_file.readline()
                    if not line or line == b'\r\n':
                        break
                print("Attempting to update page...")
                updatePage(cl, RGB)
                break


            LED_ACTIVE = True
        # Deactivate LED
        elif command == "d":
            if LED_ACTIVE:
                blue_led.deinit()
                red_led.deinit()
                green_led.deinit()
                LED_ACTIVE = False
            else:
                print("LED has not been activated!")
                pass
        # Display measurement stream
        elif command == "v":
            VERBOSE = not VERBOSE

        else:
            command = None
            pass


try:
    do_connect()
    # Create socket and listen for connections
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)
    print("Initiating main loop...")
    loop(socket=s)


except KeyboardInterrupt:
    print("Program terminated")
finally:
    measure_timer.deinit()
    if LED_ACTIVE:
        blue_led.deinit()
        red_led.deinit()
        green_led.deinit()





