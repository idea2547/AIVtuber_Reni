import urllib
import urllib.parse
import urllib.request
import requests
import openai
import winsound
import sys
import pytchat
import time
import re
import pyaudio
import keyboard
import wave
import threading
import pyperclip
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from config import *
from katakana import *
from translate import *
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Create a new browser instance
driver = webdriver.Chrome()

# Load the website
url = "https://voice.botnoi.ai/tts/conversation"
driver.get(url)



input("have you login botnoi?")


# Locate the playsound button and click it
""" playsound_button = driver.find_element_by_css_selector(".playsound")
playsound_button.click() """

# Clear the text inside the textarea
# textarea.clear()


url = "https://api-voice.botnoi.ai/api/service/generate_audio"

headers = {
    'Botnoi-Token': 'INPUT_KEY',
    'Content-Type': 'application/json'
}

# to help the CLI write unicode characters to the terminal
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

# use your own API Key, you can get it from https://openai.com/. I place my API Key in a separate file called config.py
openai.api_key = 'INPUT_KEY'

# Lore for your assistant
with open("lore.txt", "r", encoding="utf-8") as f:
    lore = f.read()

# initialize the conversation history to make your assistant have a short-term memory
conversation = [{"role": "system", "content": lore}]
mode = 0
total_characters = 0
chat = ""
chat_now = ""
chat_prev = ""
is_Speaking = False

# function to get the user's input audio
def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    WAVE_OUTPUT_FILENAME = "input.wav"
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    print("Recording...")
    while keyboard.is_pressed('RIGHT_SHIFT'):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Stopped recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    transcribe_audio("input.wav")

# function to transcribe the user's audio
def transcribe_audio(file):
    global chat_now
    try:
        audio_file= open(file, "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        chat_now = transcript.text
        print ("Question: " + chat_now)
    except:
        print("Error transcribing audio")
        return

    # Optional: translate the user's input to English. If your are an English speaker, you can skip this step
    # I translate the user's input to English because it will be easier for the translator to translate from EN to JP, compared to translating from ID to JP
    result = translate_google(chat_now, "TH", "EN")
    conversation.append({"role": "user", "content": result})
    print("Pass")
    openai_answer()

# function to get an answer from OpenAI
def openai_answer():
    global total_characters, conversation

    # get the total number of characters in the conversation history
    total_characters = sum(len(d['content']) for d in conversation)

    # if the total number of characters is greater than 4000, remove the second dictionary from the list. Because OpenAI's API has a limit of 4000 characters
    while total_characters > 4000 and len(conversation) > 1:
        # remove the second dictionary from the list
        conversation.pop(1)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
        max_tokens=128,
        temperature=1,
        top_p=0.9
    )
    conversation.append({"role": "assistant", "content": response['choices'][0]['message']['content']})
    message = response['choices'][0]['message']['content']
    translate_text(message)

# function to capture livechat from youtube
def get_livechat(video_id):
    global chat

    live = pytchat.create(video_id=video_id)
    while live.is_alive():
        for c in live.get().sync_items():
            # Ignore chat from the streamer and Nightbot, change this if you want to include the streamer's chat
            if c.author.isChatOwner or c.author.name == 'Nightbot':
                continue
            # Remove emojis from the chat
            chat_raw = re.sub(r':[^\s]+:', '', c.message)
            chat = c.author.name + ' : ' + chat_raw
            if len(chat_raw) > 5:
                # chat_author makes the chat look like this: "Nightbot: Hello". So the assistant can respond to the user's name
                chat_author = c.author.name + ' berkata: ' + chat_raw
                print(chat_author)
                conversation.append({"role": "user", "content": chat_author})
            time.sleep(1)

def translate_text(text):
    print("pass")
    # result_th will act as subtitle for the viewer
    result_th = translate_google(text, "EN", "TH")
    print("ID Answer: " + result_th)
    # result_jp will be the string to be converted to audio
    result_jp = translate_google(text, "EN", "JA")
    # print("JP Answer: " + result_jp)
    speech_text(result_jp, result_th)

def speech_text(result_jp, result_th):

    pyperclip.copy(result_th)

    # payload = {"text": result_th, "speaker":"10", "volume":1, "speed":1, "type_media":"wav"}
    # You need to run VoicevoxEngine.exe first before running this script
    global is_Speaking
    # Convert the text to katakana. Example: ORANGE -> オレンジ, so the voice will sound more natural
    # katakana_text = katakana_converter(result_jp)
    
    # You can change the voice to your liking. You can find the list of voices on speaker.json
    # or check the website https://voicevox.hiroshiba.jp
    """ params_encoded = urllib.parse.urlencode({'text': katakana_text, 'speaker': 46})
    request = requests.post(f'http://127.0.0.1:50021/audio_query?{params_encoded}')
    params_encoded = urllib.parse.urlencode({'speaker': 46, 'enable_interrogative_upspeak': True})
    request = requests.post(f'http://127.0.0.1:50021/synthesis?{params_encoded}', json=request.json()) """

    # response = requests.request("POST", url, headers=headers, json=payload)
    # response = {'text': 'รูมู ซี', 'audio_url': 'https://botnoi-dictionary.s3.amazonaws.com:443/b85b012cc96903f9298784ac8628a784ed40686f1760dbeaccaefcbef95895eb_03242023125853647087.wav'}
    # print(response.json())

    """ with open("output.wav", "wb") as outfile:
        outfile.write(requests.get(response.json()['audio_url']).content) """
    

    # Find the textarea element by id
    textarea = driver.find_element_by_id("textarea_inputbox")
    textarea.clear()

    time.sleep(1)

    textarea.send_keys(Keys.CONTROL, 'v')

    """ textarea.click()

    actions = ActionChains(driver)
    actions.send_keys(result_th).perform() """

    time.sleep(1)


    dropdown_button = driver.find_element_by_css_selector("span.btn-select-voice")
    dropdown_button.click()

    person_box = driver.find_element_by_class_name("personbox")
    person_box.click()

    """ speed_set = driver.find_element_by_css_selector("span.select-speed-tooltip")
    speed_set.click()

    # Wait for the element to be visible and clickable
    element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//span[text()="x1.50"]'))
    )

    # Click on the element
    element.click() """

    button = driver.find_element_by_css_selector(".btn-toolbar-create")
    button.click()

    # Assuming you have initialized the webdriver and navigated to the webpage
    wait = WebDriverWait(driver, 30)
    play_sound_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".playsound")))

    # Locate the playsound button and click it
    playsound_button = driver.find_element_by_css_selector(".playsound")

    # Extract the URL of the audio file from the playsound button
    # audio_url = playsound_button.get_attribute("audio-url")

    # Download the audio file
    """ response = requests.get(audio_url)
    with open("output.wav", "wb") as outfile:
        outfile.write(response.content) """
    
    # output.txt will be used to display the subtitle on OBS
    with open("output.txt", "w", encoding="utf-8") as outfile:
        try:
            text = result_th
            words = text.split()
            lines = [words[i:i+10] for i in range(0, len(words), 10)]
            for line in lines:
                outfile.write(" ".join(line) + "\n")
        except:
            print("Error writing to output.txt")

    # chat.txt will be used to display the chat/question on OBS
    with open("chat.txt", "w", encoding="utf-8") as outfile:
        global chat_now
        try:
            words = chat_now.split()
            lines = [words[i:i+10] for i in range(0, len(words), 10)]
            for line in lines:
                outfile.write(" ".join(line) + "\n")
        except:
            print("Error writing to chat.txt")


    # is_Speaking is used to prevent the assistant speaking more than one audio at a time
    is_Speaking = True
    play_sound_button.click()

    print("pass")
    # winsound.PlaySound("output.wav", winsound.SND_FILENAME)
    is_Speaking = False
    print("false")

    button = driver.find_element_by_css_selector(".btn-toolbar-create")
    button.click()
    # Clear the text files after the assistant has finished speaking
    with open ("output.txt", "w") as f:
        f.truncate(0)
    with open ("chat.txt", "w") as f:
        f.truncate(0)

def preparation():
    global conversation, chat_now, chat, chat_prev
    while True:
        # If the assistant is not speaking, and the chat is not empty, and the chat is not a command, and the chat is not the same as the previous chat
        # then the assistant will answer the chat
        chat_now = chat
        if is_Speaking == False and len(conversation) > 1 and not chat.startswith("!") and chat_now != chat_prev:
            chat_prev = chat_now
            openai_answer()
        time.sleep(1)

if __name__ == "__main__":
        
        # You can change the mode to 1 if you want to record audio from your microphone
        # or change the mode to 2 if you want to capture livechat from youtube
        mode = input("Mode (1-Mic, 2-Youtube Live): ")

        if mode == "1":
            print("Press and Hold Right Shift to record audio")
            while True:
                if keyboard.is_pressed('RIGHT_SHIFT'):
                    record_audio()
            
        elif mode == "2":
                live_id = input("Livestream ID: ")
                # Threading is used to capture livechat and answer the chat at the same time
                t = threading.Thread(target=preparation)
                t.start()
                get_livechat(live_id)


