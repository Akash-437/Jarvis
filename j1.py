import threading
import queue
import speech_recognition as sr
import pyttsx3
import wikipedia
import tkinter as tk
from tkinter import scrolledtext

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
                    audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                self.callback(text)
            except sr.UnknownValueError:
                pass
            except sr.RequestError:
                print("Could not request results from speech recognition service")

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
                text = self.text_queue.get(timeout=1)
                self.engine.say(text)
                self.engine.runAndWait()
            except queue.Empty:
                pass

    def stop(self):
        self.is_running = False

class AssistantGUI:
    def __init__(self, master):
        self.master = master
        master.title("Voice Assistant")
        master.geometry("400x300")

        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=40, height=10)
        self.text_area.pack(padx=10, pady=10)

        self.start_button = tk.Button(master, text="Start Listening", command=self.toggle_listening)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(master, text="Stop Processing", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.text_queue = queue.Queue()
        self.tts_thread = TextToSpeechThread(self.text_queue)

        self.is_listening = False
        self.is_processing = False

    def toggle_listening(self):
        if not self.is_listening:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        self.is_listening = True
        self.start_button.config(text="Stop Listening")
        self.speech_thread = SpeechRecognitionThread(self.on_text_detected)
        self.speech_thread.start()
        self.tts_thread.start()
        self.add_to_text_area("Assistant: Listening started. How can I help you?")
        self.text_queue.put("Listening started. How can I help you?")

    def stop_listening(self):
        self.is_listening = False
        self.start_button.config(text="Start Listening")
        self.speech_thread.stop()
        self.tts_thread.stop()
        self.add_to_text_area("Assistant: Listening stopped.")
        self.text_queue.put("Listening stopped.")

    def on_text_detected(self, text):
        self.add_to_text_area(f"You: {text}")
        if "exit" in text.lower():
            self.master.quit()
        elif "search" in text.lower():
            self.stop_button.config(state=tk.NORMAL)
            self.is_processing = True
            query = text.lower().replace("search", "").strip()
            self.add_to_text_area(f"Assistant: Searching for '{query}'...")
            self.text_queue.put(f"Searching for {query}")
            result = self.get_wikipedia_summary(query)
            if not self.is_processing:
                return
            self.add_to_text_area(f"Assistant: {result}")
            self.text_queue.put(result)
            self.is_processing = False
            self.stop_button.config(state=tk.DISABLED)
        else:
            response = "I'm sorry, I can only perform searches at the moment. Please say 'search' followed by your query."
            self.add_to_text_area(f"Assistant: {response}")
            self.text_queue.put(response)

    def stop_processing(self):
        self.is_processing = False
        self.stop_button.config(state=tk.DISABLED)
        self.add_to_text_area("Assistant: Processing stopped.")
        self.text_queue.put("Processing stopped.")

    def get_wikipedia_summary(self, query):
        try:
            return wikipedia.summary(query, sentences=2)
        except wikipedia.exceptions.DisambiguationError as e:
            return f"There are multiple results for {query}. Please be more specific."
        except wikipedia.exceptions.PageError:
            return f"Sorry, I couldn't find any information about {query}."

    def add_to_text_area(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    assistant = AssistantGUI(root)
    root.mainloop()