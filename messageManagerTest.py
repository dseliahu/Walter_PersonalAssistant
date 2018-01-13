
import messageManager as m
import requests
import os
import urllib
from datetime import datetime


IFTTT_API_KEY = os.getenv("IFTTT_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")

if IFTTT_API_KEY == None or WOLFRAM_API_KEY == None:
  print("Could not load necessary api keys")
  exit(1)


def lightHandler(args):
  if "value" in args:
    value = args["value"]
    if value == "on":
      print("Ok, I'll turn the lights on.")
      r = requests.post("https://maker.ifttt.com/trigger/dannyBedroomLights_on/with/key/" + IFTTT_API_KEY)

    if value == "off" or value == "out":
      print("Ok, I'll turn the lights off.")
      r = requests.post("https://maker.ifttt.com/trigger/dannyBedroomLights_off/with/key/" + IFTTT_API_KEY)

def musicHandler(args):
  print("in musicHandler")



def timeHandler(args):
    currentTime = datetime.now().strftime("%A, %B %d at %I:%M%p")
    print(currentTime)

def defaultHandler(message):
  params = {"appid" :WOLFRAM_API_KEY, "i":message, "units":"imperial"}
  url_params = urllib.parse.urlencode(params)
  url = "http://api.wolframalpha.com/v1/result?" + url_params
  r = requests.get(url)
  if r.status_code == 200:
    print(r.text)
  else:
    print("I'm sorry, I don't know how to handle that yet")



manager = m.messageManager()
manager.newRule("turn the lights <value>", lightHandler)
manager.newRule("turn <value> the lights", lightHandler)
manager.newRule("lights <value>", lightHandler)

manager.newRule("what time is it", timeHandler)

manager.setDefaultCallback(defaultHandler)
# manager.newRule("play <song> by <artist>", musicHandler)

while True:
  message = input("Type a message (Q to exit): \n")
  if message == 'Q':
    break
  else:
    manager.processMessage(message)
