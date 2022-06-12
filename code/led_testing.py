# Escreve o teu código aqui :-)
from machine import Pin, PWM

v = 0
led_red = PWM(Pin(22), freq=1000, duty=v)
led_green = PWM(Pin(21), freq=1000, duty=v)
led_blue = PWM(Pin(18), freq=1000, duty=v)

def loop():
    global v, led_red, led_green, led_blue
    while True:
        string = input("enter new duty \n")
        led_select = string[0]
        duty_val = int(string[1:])

        duty_val = 255 if duty_val > 255 else duty_val
        duty_val = 0 if duty_val < 0 else duty_val

        if led_select == "r":
            led_red.duty(duty_val)
        elif led_select == "g":
            led_green.duty(duty_val)
        elif led_select == "b":
            led_blue.duty(duty_val)
        else:
            pass

        pass

try:
    loop()
except KeyboardInterrupt:
    print("Program terminated")
finally:
    led_red.deinit()
    led_green.deinit()
    led_blue.deinit()


