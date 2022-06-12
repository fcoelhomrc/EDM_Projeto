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



def main_loop(converters):
    # Unpack converters for adjusting output range
    calibrated = False
    if None not in converters:
        calibrated = True
        
    # Measurement variables
    current_count = 0 # counts number of full cycles
    cache = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0} # stores latest measurements
    measure_interval = 100 # ms
    filters = ["clear", "red", "green", "blue"]
    filter_index = 0 
    
    def get_measurement(tag):
        # Get measurement
        measurement = current_count/measure_interval # kHz
        
        if filter_index == 0: # Clear photodiode
            # sensor_calibration(cache) # Adjust scale according to calibration
            print(f"Results: {cache}") 
            cache[filters[filter_index]] = measurement # Store new clear value
        else: # RGB photodiodes
            if calibrated:
                converter = converters[filter_index - 1]
                cache[filters[filter_index]] = converter(measurement/cache["clear"]) # Convert to RGB scale
            else:
                cache[filters[filter_index]] = (measurement/cache["clear"])*255 # Convert to RGB scale
        
        # Cycle through filters
        filter_index = (filter_index + 1)%4
        select_filter(filters[filter_index])
        # Reset counter
        current_count = 0

    def increment(tag):
        current_count += 1
        # Sensor output
        sensor_signal = Pin(19, Pin.IN)
        
    # Measurement cycle
    measure_timer = Timer(-1)
    measure_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement)
    sensor_signal.irq(trigger=Pin.IRQ_RISING, handler=increment)

def calibrate():
    
    def get_measurement(tag):
        # Get measurement
        measurement = current_count/measure_interval # kHz
        
        if tag == cache_black:
            cache_black[filters[filter_index]] = measurement
            
        if tag == cache_white:
            cache_white[filters[filter_index]] = measurement
        
        # Cycle through filters
        filter_index = (filter_index + 1)%4
        select_filter(filters[filter_index])
        # Reset counter
        current_count = 0

    def increment(tag):
        current_count += 1
        # Sensor output
        sensor_signal = Pin(19, Pin.IN)
    
    
    # Sensor output
    sensor_signal = Pin(19, Pin.IN)
    
    # Store calibration results
    cache_black = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0} 
    cache_white = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0}
    
    # Measurement variables
    current_count = 0 # counts number of full cycles
    measure_interval = 100 # ms
    filters = ["clear", "red", "green", "blue"]
    filter_index = 0 

    # Calibration cycle
    sensor_signal.irq(trigger=Pin.IRQ_RISING, handler=increment)
    
    input("Please, place black object and press Enter to continue...")
    black_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement)
    print("Calibrating for black object...")
    sleep_ms(500)
    black_timer.deinit()
    print("Finished calibration for black object")
    
    input("Please, place white object and press Enter to continue...")
    white_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement)
    print("Calibrating for white object...")
    sleep_ms(500)
    white_timer.deinit()
    print("Finished calibration for white object")
    
    converters = []
    for color in ["red", "green", "blue"]:
        # Convert to percentages
        cache_black[color] /=  cache_black["clear"]
        cache_white[color] /=  cache_black["clear"]
        # Define functions for converting to correct measuring ranges
        converter = lambda x : int(255/(cache_white[color] - cache_black[color])*(x - cache_black[color]))
        converters.append(converter)
        
    print(f"Black results: {cache_black}")
    print(f"White results: {cache_white}")
    print("Calibration completed successfully!")
    return converters
    
converters = [None, None, None]
while True:
    main_loop(converters)
    command = input("Enter 'c' for calibration")
#     if command == "c":
#         converters = calibrate()
#     else:
#         pass
    


# Kill program after a certain amount of time has passed
start = ticks_ms()
while True:
    if ticks_ms() - start > 60000:
        measure_timer.deinit()
        sensor_signal.irq(trigger=Pin.IRQ_RISING, handler=(lambda tag : None))


# LED control
# blue_led = PWM(Pin(18), freq=500, duty=0)
# red_led = PWM(Pin(22), freq=500, duty=0)
# green_led = PWM(Pin(21), freq=500, duty=0)


#######################################################
# Testes




# Teste ler output sensor
def read_sensor(filter_mode):
    global out
    filter(filter_mode)
    start = ticks_ms()
    while ticks_ms() - start < 1000:
        print(out.value())



#Teste LEDS
def test_Led(pwm, duty_v):
    pwm.duty(duty_v)
    pwm.freq(100)
    sleep_ms(5000)
    pwm.deinit()

# while True:
#     test_Led(blue,200)
#     test_Led(green,200)
#     test_Led(red,200)

def test_sensor():
    print("Reading red values...")
    read_sensor("red")
    sleep_ms(1000)
    print("Reading green values...")
    read_sensor("green")
    sleep_ms(1000)
    print("Reading blue values...")
    read_sensor("blue")
    sleep_ms(1000)
    print("Reading clear values...")
    read_sensor("clear")

# test_sensor()


