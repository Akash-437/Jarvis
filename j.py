import speech_recognition as sr
import pyttsx3
import wikipedia

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_google(audio)
        return text
    except:
        print("Sorry, I didn't catch that.")
        return None

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def process_command(command):
    if "search" in command.lower():
        query = command.lower().replace("search", "").strip()
        try:
            result = wikipedia.summary(query, sentences=2)
            return result
        except:
            return "Sorry, I couldn't find information about that."
    else:
        return "I'm sorry, I don't understand that command."

def main():
    speak("Hello, I'm your basic voice assistant. How can I help you?")
    
    while True:
        command = listen()
        if command:
            response = process_command(command)
            speak(response)

if __name__ == "__main__":
    main()