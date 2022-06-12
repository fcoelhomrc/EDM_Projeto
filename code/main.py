from machine import Pin, PWM, ADC
from time import sleep_ms

s3 = Pin(4, Pin.OUT)
s2 = Pin(2, Pin.OUT)
s1 = Pin(12, Pin.OUT)
s0 = Pin(13, Pin.OUT)

out = Pin(19, Pin.IN)

blue = PWM(Pin(18))
red = PWM(Pin(10))
green = PWM(Pin(9))

blue.freq(1000)
blue.duty(512)

sleep_ms(10000)
blue.deinit()
