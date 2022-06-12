from machine import Pin, PWM, ADC
from time import sleep_ms, ticks_ms

# Selection pins
s3 = Pin(4, Pin.OUT)
s2 = Pin(2, Pin.OUT)
s1 = Pin(12, Pin.OUT)
s0 = Pin(13, Pin.OUT)

# Output frequency scaling
# 20%
s0.write(1)
s1.write(0)

# Choose filter
def filter(mode):
    global s2, s3
    if mode == "red":
        s2.write(0)
        s3.write(0)

    elif mode == "green":
        s2.write(1)
        s3.write(1)

    elif mode == "blue":
        s2.write(0)
        s3.write(1)

    elif mode == "clear":
        s2.write(1)
        s3.write(0)
    else:
        print("Invalid mode")

# Sensor output
out = Pin(19, Pin.IN)

# LED control
blue = PWM(Pin(18))
red = PWM(Pin(10))
green = PWM(Pin(9))

#Teste LEDS

def ligar_Led(pwm, duty_v):
    pwm.duty(duty_v)
    pwm.freq(100)
    sleep_ms(5000)
    pwm.deinit()

while True:
    ligar_Led(blue,200)
    ligar_Led(green,200)
    ligar_Led(red,200)



