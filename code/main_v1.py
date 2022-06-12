
    filter_index = (filter_index + 1)%4
    select_filter(filters[filter_index])
    # Reset counter
    current_count = 0

def increment(tag):
    global current_count
    current_count += 1

current_count = 0 # counts number of full cycles
cache = {"clear" : 0, "red" : 0, "green" : 0, "blue" : 0} # stores latest measurements
measure_interval = 100 # ms
filters = ["clear", "red", "green", "blue"]
filter_index = 0 

measure_timer = Timer(-1)
measure_timer.init(period=measure_interval, mode=Timer.PERIODIC, callback=get_measurement)

sensor_signal.irq(trigger=Pin.IRQ_RISING, handler=increment)


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


