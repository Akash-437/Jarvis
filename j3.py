import threading
import queue
import speech_recognition as sr
import pyttsx3
import wikipedia
import tkinter as tk
from tkinter import scrolledtext
from langdetect import detect
from googletrans import Translator

class SpeechRecognitionThread(threading.Thread):
    def __init__(self, callback):
        threading.Thread.__init__(self)
        self.callback = callback
        self.recognizer = sr.Recognizer()
        self.is_running = True

    def run(self):
        while self.is_running:
            try:
                with sr.Microphone() as source:
                    print("Listening...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=5)
                print("Audio captured, recognizing...")
                text = self.recognizer.recognize_google(audio, show_all=True)
                if text:
                    detected_text = text['alternative'][0]['transcript']
                    print(f"Recognized: {detected_text}")
                    language = detect(detected_text)
                    self.callback(detected_text, language)
            except sr.WaitTimeoutError:
                print("Listening timed out, restarting...")
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results; {e}")

    def stop(self):
        self.is_running = False

class TextToSpeechThread(threading.Thread):
    def __init__(self, text_queue):
        threading.Thread.__init__(self)
        self.text_queue = text_queue
        self.engine = pyttsx3.init()
        self.is_running = True

    def run(self):
        while self.is_running:
            try:
                text, language = self.text_queue.get(timeout=1)
                voices = self.engine.getProperty('voices')
                matching_voice = next((v for v in voices if language in v.languages), voices[0])
                self.engine.setProperty('voice', matching_voice.id)
                self.engine.say(text)
                self.engine.runAndWait()
            except queue.Empty:
                pass

    def stop(self):
        self.is_running = False

class AssistantGUI:
    def __init__(self, master):
        self.master = master
        master.title("Multilingual Voice Assistant")
        master.geometry("400x300")

        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=40, height=10)
        self.text_area.pack(padx=10, pady=10)

        self.stop_button = tk.Button(master, text="Stop Processing", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.text_queue = queue.Queue()
        self.tts_thread = TextToSpeechThread(self.text_queue)
        self.tts_thread.start()

        self.is_processing = False
        self.translator = Translator()

        # Start listening automatically
        self.speech_thread = SpeechRecognitionThread(self.on_text_detected)
        self.speech_thread.start()

        self.add_to_text_area("Assistant: Listening started. How can I help you?")
        self.text_queue.put(("Listening started. How can I help you?", 'en'))

    def on_text_detected(self, text, language):
        self.add_to_text_area(f"You: {text}")
        if "exit" in text.lower():
            self.master.quit()
        elif "search" in text.lower():
            self.stop_button.config(state=tk.NORMAL)
            self.is_processing = True
            query = text.lower().replace("search", "").strip()
            search_message = self.translate_text(f"Searching for '{query}'...", language)
            self.add_to_text_area(f"Assistant: {search_message}")
            self.text_queue.put((search_message, language))
            result = self.get_wikipedia_summary(query)
            if not self.is_processing:
                return
            translated_result = self.translate_text(result, language)
            self.add_to_text_area(f"Assistant: {translated_result}")
            self.text_queue.put((translated_result, language))
            self.is_processing = False
            self.stop_button.config(state=tk.DISABLED)
        else:
            response = "I'm sorry, I can only perform searches at the moment. Please say 'search' followed by your query."
            translated_response = self.translate_text(response, language)
            self.add_to_text_area(f"Assistant: {translated_response}")
            self.text_queue.put((translated_response, language))

    def stop_processing(self):
        self.is_processing = False
        self.stop_button.config(state=tk.DISABLED)
        stop_message = self.translate_text("Processing stopped.", 'en')
        self.add_to_text_area(f"Assistant: {stop_message}")
        self.text_queue.put((stop_message, 'en'))

    def get_wikipedia_summary(self, query):
        try:
            return wikipedia.summary(query, sentences=2)
        except wikipedia.exceptions.DisambiguationError as e:
            return f"There are multiple results for {query}. Please be more specific."
        except wikipedia.exceptions.PageError:
            return f"Sorry, I couldn't find any information about {query}."

    def translate_text(self, text, target_language):
        if target_language == 'en':
            return text
        try:
            return self.translator.translate(text, dest=target_language).text
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original text if translation fails

    def add_to_text_area(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    assistant = AssistantGUI(root)
    root.mainloop()