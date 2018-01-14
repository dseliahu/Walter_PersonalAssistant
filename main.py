import messageManager as m
import snowboydecoder
import speech_recognition as sr
import signal
import os
import requests
import string
import sys
import urllib
import RPi.GPIO as GPIO
from bs4 import BeautifulSoup
from datetime import datetime

PRINT_OUTPUT = True
SPEAK_OUTPUT = True
SPEAK_INPUT = True

##### Handler Functions #######
def lightHandler(args):
    if "value" in args:
        value = args["value"]
        if value == "on":
            output("Ok, I'll turn the lights on.")
            r = requests.post("https://maker.ifttt.com/trigger/dannyBedroomLights_on/with/key/" + IFTTT_API_KEY)

        if value == "off" or value == "out":
            output("Ok, I'll turn the lights off.")
            r = requests.post("https://maker.ifttt.com/trigger/dannyBedroomLights_off/with/key/" + IFTTT_API_KEY)

def echoHandler(args):
    if "phrase" in args:
        output(args["phrase"])

def jokeHandler(args):
    output("my jokes aren't very good yet. I'm still working on them.")

def timeHandler(args):
    if "location" in args:
        location = args["location"]
        answer = askWolfram("What time is it in " + location.strip())
        output(answer)
    else:
        output(datetime.now().strftime("It's %I:%M%p"))

def dateHandler(args):
    output(datetime.now().strftime("Today is %A, %d. %B %Y"))

def whoIsHandler(args):
    if "person" in args:
        person = args["person"]
        answer = askWebKnox("who is " + person.strip())
        names = person.split(" ")
        for name in names:
            if answer.lower().count(name.lower()) > 1:
                answer = "I'm not sure about that one, sorry"
                break
        output(answer)

def whoPlaysHandler(args):
    if "person" in args and "title" in args:
        person = args["person"]
        title = args["title"]
        answer = askWebKnox("who plays " + person.strip() + " in " + title.strip())
        output(answer)

def sayHiHandler(args):
    if "person" in args:
        person = args["person"]
        answer = "Hello " + person + "! It is very nice to meet you."
        output(answer)

def defaultHandler(message):
    answer = askWolfram(message)
    output(answer)


###### snowboy callbacks ########
def audioRecorderCallback(fname):
    global manager
    print('.', end='', flush=True)
    r = sr.Recognizer()
    with sr.AudioFile(fname) as source:
        audio = r.record(source)  # read the entire audio file
    # recognize speech using Google Speech Recognition
    try:
        # for testing purposes, we're just using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        # instead of `r.recognize_google(audio)`
        manager.processMessage(r.recognize_google(audio))
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))

    os.remove(fname)
    GPIO.output(LED_PIN, GPIO.LOW)

def detectedCallback():
    print('.', end='', flush=True)
    GPIO.output(LED_PIN, GPIO.HIGH)

def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted

###### Helper functions #######
def output(message):
    GPIO.output(LED_PIN, GPIO.LOW)
    if PRINT_OUTPUT:
        print(message)

    if SPEAK_OUTPUT:
        if sys.platform == "darwin":
            cmd = "say " + message.strip().replace('\'', '\\\'')
            print("command was: " + cmd)
            os.system(cmd)
        else:
            os.system("pico2wave -w output.wav \"" + message + "\"")
            os.system("aplay output.wav")

def askWolfram(message):
    params = {"appid":WOLFRAM_API_KEY, "i":message, "units":"imperial"}
    url_params = urllib.parse.urlencode(params)
    url = "http://api.wolframalpha.com/v1/result?" + url_params
    r = requests.get(url)
    if r.status_code == 200 and r.text != "{}":
        answer = r.text
        answer.replace("Wolfram Alpha", "Walter")
    else:
        answer = "I'm sorry, I don't know how to handle that yet."
    return answer

def askWebKnox(message):
    querryString = urllib.parse.quote_plus(message)
    url = "http://webknox.com/" + querryString
    r = requests.get(url)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        answerBox = soup.find("div", {"class": "answerBox"})
        if answerBox is not None:
            answer = answerBox.text
        if "Nothing found, sorry" in answer:
            answer = "I couldn't find anything for that one, sorry."
    else:
        answer = "I'm not sure about that one, sorry."
    return answer


####### main #########
# Global setup
interrupted = False
IFTTT_API_KEY = os.getenv("IFTTT_API_KEY")
WOLFRAM_API_KEY = os.getenv("WOLFRAM_API_KEY")
if IFTTT_API_KEY == None or WOLFRAM_API_KEY == None:
    print("Could not load necessary api keys")
    exit(1)

LED_PIN = 40
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_PIN, GPIO.OUT)

# Setup rules for message manager
manager = m.messageManager()
#lights
manager.newRule("turn the lights <value>", lightHandler)
manager.newRule("turn my lights <value>", lightHandler)
manager.newRule("turn <value> the lights", lightHandler)
manager.newRule("turn <value> my lights", lightHandler)
manager.newRule("lights <value>", lightHandler)
#say hi
manager.newRule("say hi to <person>", sayHiHandler)
#echo
manager.newRule("repeat this phrase <phrase>",  echoHandler)
manager.newRule("say <phrase>", echoHandler)
#joke
manager.newRule("tell me a joke", jokeHandler)
#time
manager.newRule("what time is it in <location>", timeHandler)
manager.newRule("whats the time in <location>", timeHandler)
manager.newRule("what time is it", timeHandler)
manager.newRule("whats the time", timeHandler)
manager.newRule("what day is it", dateHandler)
#who is
manager.newRule("who is <person>", whoIsHandler)
#who plays
manager.newRule("who plays <person> in <title>", whoPlaysHandler)
manager.newRule("who played <person> in <title>", whoPlaysHandler)
#defualt
manager.setDefaultCallback(defaultHandler)


# Configure and start snowboy
if SPEAK_INPUT:
    model = "resources/walter2.pmdl"
    # capture SIGINT signal, e.g., Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    detector = snowboydecoder.HotwordDetector(model, sensitivity=0.38)
    print('Listening... Press Ctrl+C to exit')
    detector.start(detected_callback=detectedCallback,
                   audio_recorder_callback=audioRecorderCallback,
                   interrupt_check=interrupt_callback,
                   sleep_time=0.03,
                   silent_count_threshold=6,
                   recording_timeout=60)


    detector.terminate()
else:
    while True:
        message = input("Type a message (Q to exit): \n")
        if message == 'Q':
            break
        else:
            manager.processMessage(message)
