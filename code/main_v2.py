from machine import Pin, PWM, Timer
from time import sleep_ms, ticks_ms

# Selection pins
s3 = Pin(25, Pin.OUT)
s2 = Pin(27, Pin.OUT)
s1 = Pin(23, Pin.OUT)
s0 = Pin(26, Pin.OUT)

# Output frequency scaling
# 20%
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
    global current_count, filters, filter_index, measure_interval
    global cache, dark_calib_cache
    global measure_timer, dark_calib_timer
    # Get measurement
    measurement = current_count/measure_interval # kHz
    if tag == measure_timer:
        
        if filter_index == 0: # Clear photodiode
            print(f"Results: {cache}")
            cache[filters[filter_index]] = measurement # Store new clear value
        else: # RGB photodiodes
            cache[filters[filter_index]] = (measurement/cache["clear"])*255 # Convert to RGB scale

    elif tag == calib_timer:
        print(f"Now writing value for {filters[filter_index]}...", end="\n")
        if filter_index == 0: # Clear photodiode
            dark_calib_cache[filters[filter_index]] = measurement # Store new clear value
        else: # RGB photodiodes
            dark_calib_cache[filters[filter_index]] = (measurement/dark_calib_cache["clear"])*255 # Convert to RGB scale

    # Cycle through filters
    filter_index = (filter_index + 1)%4
    select_filter(filters[filter_index])
    # Reset counter
    current_count = 0

def increment(tag):
    global current_count
    current_count += 1


cache = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0} # stores latest measurements
dark_calib_cache = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0}

current_count = 0 # counts number of full cycles
measure_interval = 500 # ms

filters = ["clear", "red", "green", "blue"]
filter_index = 0

# Operation mode: measure values constantly
measure_timer = Timer(1)
calib_timer = Timer(2)

sensor_signal.irq(trigger=Pin.IRQ_RISING, handler=increment)

def calibration():
    global measure_interval, filter_index, current_count
    global dark_calib_cache
    global dark_calib_timer
    
    print("Beginning calibration for dark values...")
    current_count = 0 # Guarantees no left over counts
    initial_filter_index = filter_index
    filter_index = 0 # Start from the first filter option
    
    calib_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement)
    while True:
        for value in dark_calib_cache.values():
            if value < 0.01:
                break
        else:
            print("Interrupting calibration timer...")
            calib_timer.deinit()
            current_count = 0 # Guarantees no left over counts
            filter_index = initial_filter_index # Restore filter option in use before calibration
            break
    print(f"Calibration results (dark): {dark_calib_cache}")

def loop():
    global measure_interval
    global measure_timer
    
    measure_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement) # Begin measurement
    while True:
        command = input("Enter 'c' to begin calibration... \n")
        if command == "c":
            print("Interrupt measurement timer...")
            measure_timer.deinit() # Stop normal measurement
            calibration() # Proceed with calibration
            print("Resume measurement timer...")
            measure_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement) # Resume measurement
        else:
            command = None
            pass


try:
    loop()
except KeyboardInterrupt:
    print("Program terminated")
finally:
    measure_timer.deinit()


# LED control
# blue_led = PWM(Pin(18), freq=500, duty=0)
# red_led = PWM(Pin(22), freq=500, duty=0)
# green_led = PWM(Pin(21), freq=500, duty=0)

