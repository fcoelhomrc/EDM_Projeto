import network
import urequests
import time
import json

# Webpage HTML
import machine
pins = [machine.Pin(i, machine.Pin.IN) for i in (0, 2, 4, 5, 12, 13, 14, 15)]

html = """<!DOCTYPE html>
<html>
    <head> <title>ESP8266 Pins</title> </head>
    <body> <h1>ESP8266 Pins</h1>
        <table border="1"> <tr><th>Pin</th><th>Value</th></tr> %s </table>
    </body>
</html>
"""



# Connect to Wi-Fi
ssid = "Galaxy A32 5G1A70"
password = "yfee4537"
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print("Connecting to network...")
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.1)
    print(" Connected!")


import socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)

while True:
    cl, addr = s.accept()
    print('client connected from', addr)
    cl_file = cl.makefile('rwb', 0)
    while True:
        line = cl_file.readline()
        if not line or line == b'\r\n':
            break
    rows = ['<tr><td>%s</td><td>%d</td></tr>' % (str(p), p.value()) for p in pins]
    response = html % '\n'.join(rows)
    cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    cl.send(response)
    cl.close()

# print("network config:", wlan.ifconfig())

# Use VoiceRSS Text-to-Speech API

def parseQuerystring(url, qs):
    query = f"?key={qs['key']}&src={qs['src']}&hl={qs['hl']}&r={qs['r']}&c={qs['c']}&f={qs['f']}"
    return url + query

url = "http://api.voicerss.org/"
querystring = {
               "key":"855df224b9e54663af317722f0a96eaf",
               "src":"Testing",
               "hl":"en-us",
               "r":"0",
               "c":"mp3",
               "f":"8khz_8bit_mono"
               }


while True:
    parsed = parseQuerystring(url, querystring)
    print(parsed)
    response = urequests.request("GET", parsed)
#     with open('test.mp3', mode='bx') as f:
#         f.write(response.content)
    print(response.status_code, response.reason)

    time.sleep(10)




