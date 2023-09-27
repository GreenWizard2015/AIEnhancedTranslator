#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import tkinter.scrolledtext as tkst
from core.worker import CWorker
# set up logging
import logging
logging.basicConfig(
  filename='debug.log', filemode='w',
  level=logging.INFO, 
  format='%(asctime)s %(levelname)s %(message)s'
)
# set up environment variables
import dotenv
dotenv.load_dotenv('.env')
dotenv.load_dotenv('.env.local', override=True)
# main app
# TODO: figure out how to enforce deep translation via UI
# TODO: add translation history
# TODO: add simple translation diff
class App(tk.Frame):
  def __init__(self, master, languages, currentLanguage=None):
    super().__init__(master)
    self._localizationMap = {}
    # predefine messages
    self._localization('Processing...')
    self._localization('Translation is not accurate and will be updated soon.')
    # set up UI
    self._master = master
    self._languages = languages
    self._currentLanguage = currentLanguage or self._languages.keys()[0]
    # set global font
    self._master.option_add("*Font", ("Arial", 16))
    self._master.title("AI Enhanced Translator")
    self._UI_init()
    self.pack()
    
    self._worker = CWorker(self)
    self._worker.start()
    return
  
  def _localization(self, text):
    res = self._localizationMap.get(text)
    if res is None:
      self._localizationMap[text] = res = tk.StringVar(value=text)
    return res

  def _UI_inputArea(self, owner):
    label = tk.Label(
      owner, justify="left", anchor="w",
      textvariable=self._localization("Input Text:")
    )
    label.pack(side="top", fill=tk.X)

    self._inputText = tkst.ScrolledText(owner)
    self._inputText.pack(side="top", fill=tk.BOTH, expand=tk.YES)
    self._inputText.bind("<Control-Return>", self.onForceTranslate)
    # clear on escape
    def clear(event): self._inputText.delete("1.0", tk.END)
    self._inputText.bind("<Escape>", clear)
    # focus on start
    self._inputText.focus_set()
    return
  
  def UITextFor(self, text):
    return text
  
  def _UI_languageSelection(self, owner):
    # target language selection via combobox, stick to top right corner
    self._language = ttk.Combobox(
      owner, state="readonly", width=20,
      values=list(self._languages.values())
    )
    self._language.pack(side="top", anchor="ne", padx=5, pady=5)
    self._language.bind("<<ComboboxSelected>>", self.onSelectLanguage)
    try:
      self._language.set(self._languages[self._currentLanguage])
    except tk.TclError:
      pass
    return
  
  def _UI_outputArea(self, owner):
    self._UI_languageSelection(owner)
    # fast translation
    label = tk.Label(
      owner, justify="left", anchor="w",
      textvariable=self._localization("Fast and inaccurate translation:")
    )
    label.pack(side="top", fill=tk.X)

    self._fastOutputText = tkst.ScrolledText(owner, height=15)
    self._fastOutputText.pack(side="top", fill=tk.BOTH, expand=tk.YES)

    # full translation
    label = tk.Label(
      owner, justify="left", anchor="w",
      textvariable=self._localization("Slow and improved translation:")
    )
    label.pack(side="top", fill=tk.X)

    self._fullOutputText = tkst.ScrolledText(owner)
    self._fullOutputText.pack(side="top", fill=tk.BOTH, expand=tk.YES)
    return
  
  def _UI_init(self):
    # Two vertical frames for input and output
    leftFrame = tk.Frame(self._master)
    leftFrame.pack(side="left", fill=tk.BOTH, expand=tk.YES)
    self._UI_inputArea(leftFrame)

    rightFrame = tk.Frame(self._master)
    rightFrame.pack(side="right", fill=tk.BOTH, expand=tk.YES)

    self._UI_outputArea(rightFrame)
    return
  
  def onForceTranslate(self, event):
    self._worker.forceTranslate()
    return 'break' # prevent default action
  
  # events for worker
  def userInput(self):
    currentLanguageCode = self._currentLanguage
    currentLanguage = self._languages[currentLanguageCode]
    language = {'code': currentLanguageCode, 'name': currentLanguage}
    return self._inputText.get("1.0", tk.END), language

  def startTranslate(self, force=False):
    # set output text to "Processing..."
    if force:
      self._fullOutputText.delete("1.0", tk.END)
      self._fullOutputText.insert(tk.END, self._localization("Processing...").get())
    return
  
  def fastTranslated(self, text):
    self._fastOutputText.delete("1.0", tk.END)
    self._fastOutputText.insert(tk.END, text)
    return
  
  def fullTranslated(self, text, pending):
    self._fullOutputText.delete("1.0", tk.END)
    self._fullOutputText.insert(tk.END, text)

    if pending:
      notification = self._localization(
        "Translation is not accurate and will be updated soon."
      ).get()
      self._fullOutputText.insert(tk.END, "\n----------------\n" + notification)
    return
  
  def error(self, e):
    self._fastOutputText.delete("1.0", tk.END)
    self._fullOutputText.insert(tk.END, "Error: " + str(e) + "\n")
    return
  
  def endTranslate(self):
    return
  
  def onSelectLanguage(self, event):
    language = self._language.get()
    code = next((code for code, name in self._languages.items() if name == language), None)
    if code is None: return
 
    self._currentLanguage = code
    self._worker.forceTranslate() # hack to force translation
    return
  
  def updateLocalization(self, localization):
    for k, v in localization.items():
      self._localizationMap[k].set(v)
    return
  
  def localizationStrings(self): return list(self._localizationMap.keys())
  
if '__main__' == __name__:
  app = App(
    master=tk.Tk(),
    # TODO: load languages from config
    languages={
      'sk': 'Slovak',
      'en': 'English',
      'de': 'German',
    },
    currentLanguage='sk'
  )
  app.mainloop()