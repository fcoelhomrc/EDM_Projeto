from machine import Pin, PWM, Timer
import time
import network, socket, urequests
import uasyncio as asyncio

def do_connect():
    '''
    Connects to local Wi-Fi
    '''
    essid = "MEO-F770C0" # "NOS-D610" # "Galaxy A32 5G1A70"
    password = "7cdd0a29c1" # "fbe228d0bc19"  # "yfee4537"

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print(wlan.scan())
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(essid, password)
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

client = None
async def acceptConnection(socket):
    '''
    Whenever no client is connected, attempts to accept incoming connections
    '''
    global html, client
    while True:
        if client is None:
            cl, addr = socket.accept()
            client = cl # Update client
            print('Client connected from', addr)
            await asyncio.sleep_ms(5)
        else:
            await asyncio.sleep_ms(5)


def parseQuerystring(url, qs):
    '''
    Parse a dictionary containing the query parameters
    and write them to the url
    '''
    query = f"?key={qs['key']}&src={qs['src']}&hl={qs['hl']}&r={qs['r']}&c={qs['c']}&f={qs['f']}"
    return url + query

def getHue(RGB_values):
    '''
    Calculates hue from RGB values
    Source: "https://www.youtube.com/watch?v=BxEsEXsOJyA"
    '''
    R, G, B = tuple(RGB_values)

    if R < 20 and G < 20 and B < 20:
        return "black"
    if R > 230 and G > 230 and B > 230:
        return "white"

    R /= 255; G /= 255; B /= 255; # Normalized RGB values
    mn = min([R, G, B])
    mx = max([R, G, B])
    cr = mx - mn
    eps = 0.01 # Avoid floating point comparision
    if cr == 0:
        hue = -1 # Hue is undefined
    else:
        R1 = (( (mx - R) / 6 ) + (cr / 2)) / cr
        G1 = (( (mx - G) / 6 ) + (cr / 2)) / cr
        B1 = (( (mx - B) / 6 ) + (cr / 2)) / cr
        if  abs(R - mx) < eps:
            hue = B1-G1
        elif abs(G - mx) < eps:
            hue = 1/3 + R1 - B1
        elif abs(B - mx) < eps:
            hue = 2/3 + G1 - R1
        # Wrap so hue is between 0, 1
        if hue < 0:
            hue += 1
        if hue > 1:
            hue -= 1
        return int(hue * 360) # Convert to degrees

colornames = {
              0 : "red",
              1 : "orange",
              2 : "yellow",
              3 : "chartreuse",
              4 : "green",
              5 : "turquoise",
              6 : "cyan",
              7 : "azure",
              8 : "blue",
              9 : "purple",
              10 : "magenta",
              11 : "crimson"
             }

def getColorName(RGB_values):
    '''
    Given RGB values, return a color name based upon pre-set ranges
    '''
    global colornames
    hue = getHue(RGB_values)
    print(f"Hue value: {hue} degrees", end="\n")
    if type(hue) is not int:
        name = hue
        return name # Either black or white was detected
    else:
        hue = (hue + 15)%360 # Shift for fitting defined color intervals
        index = int(hue*12/360) # Select which interval hue falls into
        name = colornames[index] # Pick appropriate color
        return name

def convertTTS(name):
    '''
    Requests the VoiceRSS API for the color name audio
    '''
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
    with open("tts.mp3", mode="wb") as file:
        print("Writing .mp3 ...")
        file.write(api_response.content)
    print("Finished writing file")

# Fetch HTML for the web page
with open("page.txt", mode="r") as file:
    html = file.read()
def updatePage(client, rgb_values):
    '''
    Updates the page with the currently measured color RGB value and text-to-speech color name
    '''
    global html
    cl_file = client.makefile('rwb', 0)
    while True:
        line = cl_file.readline()
        if not line or line == b'\r\n':
            break
    name = getColorName(rgb_values)
    # Generate TTS audio
    convertTTS(name)
    # Update HTML with new color
    index = html.find("rgb")
    new_rgb = f"rgb({rgb_values[0]:03d}, {rgb_values[1]:03d}, {rgb_values[2]:03d})"
    html = html[:index] + new_rgb + html[index+18:]
    # Send page HTML
    print("Sending HTML update...")
    client.send('HTTP/1.0 200 OK content-type: text/html\r\n\r\n')
    client.send(html)
    time.sleep_ms(50)
    # Send audio file
    print("Sending .mp3 update...")
    client.send('HTTP/1.0 200 OK content-type: audio/mpeg')
    with open("tts.mp3", "rb") as file:
        audio = file.read()
        client.send(audio)
    time.sleep_ms(50)
    print("Closing connection...")
    client.close()


# Selection pins
s3 = Pin(25, Pin.OUT)
s2 = Pin(27, Pin.OUT)
s1 = Pin(23, Pin.OUT)
s0 = Pin(26, Pin.OUT)

# Output frequency scaling
# 20% (s0 = 1, s1 = 0)
#  2% (s0 = 0, s1 = 1)
s0.value(1)
s1.value(0)

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
    '''
    After a given time is elapsed, obtains the sensor output frequency
    from the full-cycle counter
    Manages both standard measurements and calibration
    '''
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
    '''
    Updates a counter in every signal rise (keeping track of the number of full cycles elapsed)
    '''
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
LED_ENABLED = False # Whether the LED will be updated or not
VERBOSE = True # Whether we print each measurement or not
CONNECTED = False

# Input signal from sensor
# PWM with 50% duty and light intensity encoded in its frequency
sensor_signal.irq(trigger=Pin.IRQ_RISING, handler=increment) # Counts full cycles

def calibration():
    '''
    Calibrates to set black (0, 0, 0) and white (255, 255, 255) RGB values
    from the sensor frequency readings
    '''
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

async def loop():
    '''
    Main loop for controlling the program
    '''
    global measure_interval
    global measure_timer
    global red_led, green_led, blue_led
    global client
    global LED_ACTIVE, LED_ENABLED, VERBOSE, CONNECTED

    measure_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement) # Begin measurement
    while True:
        command = input("Enter 'c' to begin calibration... \n" +
                        "Enter 'a' to activate LED and update web page... \n" +
                        "Enter 'd' to deactivate LED... \n" +
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
            print(f"Duty values: R = {DR}, G = {DG}, B = {DB}")
            # Control pins for RGB LED
            if LED_ENABLED:
                if not LED_ACTIVE:
                    red_led = PWM(Pin(22), freq=500, duty=DR)
                    green_led = PWM(Pin(21), freq=500, duty=DG)
                    blue_led = PWM(Pin(18), freq=500, duty=DB)
                    LED_ACTIVE = True
                else:
                    red_led.duty(DR)
                    green_led.duty(DG)
                    blue_led.duty(DB)
            ################################################################################
            if client is not None:
                print("Attempting to update page...")
                updatePage(client, RGB)
                client = None


        # Deactivate LED
        elif command == "d":
            LED_ENABLED = not LED_ENABLED
            print(f"The LED is now {'enabled' if LED_ENABLED else 'disabled'}...", end="\n")
            if LED_ACTIVE:
                blue_led.deinit()
                red_led.deinit()
                green_led.deinit()
                LED_ACTIVE = False
        # Display measurement stream
        elif command == "v":
            VERBOSE = not VERBOSE

        else:
            command = None
            pass

        await asyncio.sleep_ms(5)
try:
    # Connect to local Wi-Fi
    do_connect()
    # Create socket and listen for connections
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on', addr)
    print("Initiating main loop...")
    event_loop = asyncio.get_event_loop()
    event_loop.create_task(acceptConnection(s))
    event_loop.create_task(loop())
    event_loop.run_forever()
except KeyboardInterrupt:
    print("Program terminated")
finally:
    s.close()
    measure_timer.deinit()
    if LED_ACTIVE:
        blue_led.deinit()
        red_led.deinit()
        green_led.deinit()





