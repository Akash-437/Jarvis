import threading
import queue
import speech_recognition as sr
import pyttsx3
import wikipedia
import tkinter as tk
from tkinter import scrolledtext
import time

class ContinuousSpeechRecognitionThread(threading.Thread):
    def __init__(self, callback):
        threading.Thread.__init__(self)
        self.callback = callback
        self.recognizer = sr.Recognizer()
        self.is_running = True

    def run(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            while self.is_running:
                try:
                    print("Listening...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    print("Audio captured, recognizing...")
                    text = self.recognizer.recognize_google(audio, language="en-US")
                    print(f"Recognized: {text}")
                    self.callback(text)
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage

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
        master.title("Continuous Listening English Voice Assistant")
        master.geometry("500x400")

        self.text_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=50, height=20)
        self.text_area.pack(padx=10, pady=10)

        self.text_queue = queue.Queue()
        self.tts_thread = TextToSpeechThread(self.text_queue)
        self.tts_thread.start()

        self.speech_thread = ContinuousSpeechRecognitionThread(self.on_text_detected)
        self.speech_thread.start()

        self.add_to_text_area("Assistant: Listening started. How can I help you?")
        self.text_queue.put("Listening started. How can I help you?")

    def on_text_detected(self, text):
        self.add_to_text_area(f"You: {text}")
        
        if "exit" in text.lower():
            self.master.quit()
        elif "search" in text.lower():
            query = text.lower().replace("search", "").strip()
            self.perform_search(query)
        elif "stop" in text.lower():
            self.add_to_text_area("Assistant: Stopping current action.")
            self.text_queue.put("Stopping current action.")
        else:
            response = "I'm sorry, I didn't understand that command. You can say 'search' followed by a topic, or 'exit' to close the program."
            self.add_to_text_area(f"Assistant: {response}")
            self.text_queue.put(response)

    def perform_search(self, query):
        self.add_to_text_area(f"Assistant: Searching for '{query}'...")
        self.text_queue.put(f"Searching for {query}")
        result = self.get_wikipedia_summary(query)
        self.add_to_text_area(f"Assistant: {result}")
        self.text_queue.put(result)

    def get_wikipedia_summary(self, query):
        try:
            return wikipedia.summary(query, sentences=2)
        except wikipedia.exceptions.DisambiguationError as e:
            options = e.options[:5]  # Limit to first 5 options
            return f"There are multiple results for '{query}'. Possible matches: {', '.join(options)}. Please be more specific."
        except wikipedia.exceptions.PageError:
            return f"Sorry, I couldn't find any information about '{query}'."
        except Exception as e:
            return f"An error occurred while searching: {str(e)}"

    def add_to_text_area(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    assistant = AssistantGUI(root)
    root.mainloop()