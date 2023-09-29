#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
import tkinter.scrolledtext as tkst
import json, os, logging
from core.worker import CWorker
import dotenv

# main app
# TODO: add translation history
# TODO: add simple translation diff
class App(tk.Frame):
  def __init__(self, master, languages, configs):
    super().__init__(master)
    self._lastAIResult = None
    self._configs = configs
    self._localizationMap = {}
    # predefine messages
    self._localization('Processing...')
    self._localization('Translation is not accurate and will be updated soon.')
    # set up UI
    self._master = master
    self._languages = languages
    self._currentLanguage = self._configs.get('language') or 'en'
    # set global font
    self._master.option_add("*Font", ("Arial", 14))
    self._master.title("AI Enhanced Translator")
    self._master.geometry("800x600")
    self._UI_init()
    
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
    label.grid(row=0, column=0, sticky="ew")

    self._inputText = tkst.ScrolledText(owner, wrap=tk.WORD)
    self._inputText.grid(row=1, column=0, sticky="nsew")
    self._inputText.bind("<Control-Return>", self.onForceTranslate)
    # clear on escape
    def clear(event): self._inputText.delete("1.0", tk.END)
    self._inputText.bind("<Escape>", clear)
    # focus on start
    self._inputText.focus_set()

    # configure grid
    owner.grid_columnconfigure(0, weight=1)
    owner.grid_rowconfigure(1, weight=1)
    return
  
  def _UI_languageSelection(self, owner):
    # target language selection via combobox, stick to top right corner
    self._language = ttk.Combobox(
      owner, state="readonly", width=20,
      values=list(self._languages.values())
    )
    self._language.bind("<<ComboboxSelected>>", self.onSelectLanguage)
    try:
      self._language.set(self._languages[self._currentLanguage])
    except tk.TclError:
      pass
    return self._language

  def _UI_fastTranslation(self, owner):
    label = tk.Label(
      owner, justify="left", anchor="w",
      textvariable=self._localization("Fast and inaccurate translation (Google Translate):")
    )
    label.pack(side="top", fill=tk.X)

    self._fastOutputText = tkst.ScrolledText(owner, wrap=tk.WORD, foreground="darkgrey")
    self._fastOutputText.pack(side="top", fill=tk.BOTH, expand=tk.YES)
    return
  
  def _UI_fullTranslation(self, owner):
    label = tk.Label(
      owner, justify="left", anchor="w",
      textvariable=self._localization("Slow and improved translation (ChatGPT/AI):")
    )
    label.pack(side="top", fill=tk.X)
    # Button "Refine" to force deep translation, disabled by default
    self._refineBtn = btn = tk.Button(
      owner, state=tk.DISABLED,
      command=self.onRefine,
      textvariable=self._localization("Refine"),
    )
    btn.pack(side="bottom", padx=5, pady=5, anchor="e")

    self._fullOutputText = tkst.ScrolledText(owner, wrap=tk.WORD)
    self._fullOutputText.pack(side="top", fill=tk.BOTH, expand=tk.YES)
    return
  
  def _UI_outputArea(self, owner):
    # 3 rows, 1 column. First row always same height, second half of third row
    owner.grid_columnconfigure(0, weight=1)
    owner.grid_rowconfigure(0, weight=0)
    owner.grid_rowconfigure(1, weight=2)
    owner.grid_rowconfigure(2, weight=1)
    owner.grid_rowconfigure(3, weight=0)
    # language selection
    self._UI_languageSelection(owner).grid(row=0, column=0, sticky="ne")
    # fast translation frame
    fastTranslationFrame = tk.Frame(owner)
    fastTranslationFrame.grid(row=1, column=0, sticky="nsew")
    self._UI_fastTranslation(fastTranslationFrame)
    # full translation frame
    fullTranslationFrame = tk.Frame(owner)
    fullTranslationFrame.grid(row=2, column=0, sticky="nsew")
    self._UI_fullTranslation(fullTranslationFrame)

    # switch API key
    btn = tk.Button(
      owner, command=self.onSwitchAPIKey,
      textvariable=self._localization("Switch API key")
    )
    btn.grid(row=3, column=0, pady=5)
    return
  
  def _UI_init(self):
    # 1 row, 2 columns
    self._master.grid_columnconfigure((0,1), weight=1)
    self._master.grid_rowconfigure(0, weight=1)
    # Two vertical frames for input and output
    leftFrame = tk.Frame(self._master)
    leftFrame.grid(row=0, column=0, sticky="nsew")
    self._UI_inputArea(leftFrame)

    rightFrame = tk.Frame(self._master)
    rightFrame.grid(row=0, column=1, sticky="nsew")
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
    return {
      'language': language,
      'text': self._inputText.get("1.0", tk.END).strip(),
    }

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
  
  def fullTranslated(self, translationResult):
    self._lastAIResult = translationResult
    self._refineBtn.config(state=tk.DISABLED if translationResult.pending else tk.NORMAL)

    self._fullOutputText.delete("1.0", tk.END)
    self._fullOutputText.insert(tk.END, translationResult.translation)

    if translationResult.pending:
      notification = self._localization(
        "Translation is not accurate and will be updated soon."
      ).get()
      self._fullOutputText.insert(tk.END, "\n----------------\n" + notification)
    return
  
  def error(self, e):
    self._fullOutputText.delete("1.0", tk.END)
    self._fullOutputText.insert(tk.END, "Error: " + str(e) + "\n")
    return
  
  def endTranslate(self):
    return
  
  def onSelectLanguage(self, event):
    language = self._language.get()
    code = next((code for code, name in self._languages.items() if name == language), None)
    if code is None: return
    # discard AI result and disable refine button
    self._lastAIResult = None
    self._refineBtn.config(state=tk.DISABLED)
    # update other stuff
    self._currentLanguage = code
    self._configs['language'] = code
    self._worker.forceTranslate() # hack to force translation
    return
  
  def updateLocalization(self, localization):
    for k, v in localization.items():
      self._localizationMap[k].set(v)
    return
  
  def localizationStrings(self): return list(self._localizationMap.keys())

  def onSwitchAPIKey(self):
    newKey = simpledialog.askstring(
      'Switch API key',
      'Enter new API key:',
      parent=self._master
    )
    if newKey is None: return
    self._worker.bindAPI(newKey)
    return
  
  def configs(self): return self._configs

  def onRefine(self, event=None):
    # check if refine button is enabled
    if tk.DISABLED == self._refineBtn['state']: return 'break' # prevent unwanted action

    self._worker.refine(self._lastAIResult)
    self._refineBtn.config(state=tk.DISABLED)
    return 'break'
# End of class

def main():
  # set up logging
  logging.basicConfig(
    filename='debug.log', filemode='w',
    level=logging.INFO, 
    format='%(asctime)s %(levelname)s %(message)s'
  )
  # set up environment variables
  if os.path.exists('.env.local'): dotenv.load_dotenv('.env.local', override=True)

  # load languages from data/languages.json
  with open('data/languages.json', 'r') as f: languages = json.load(f)
  # load configs
  configs = {}
  try:
    with open('data/configs.json', 'r') as f: configs = json.load(f)
  except: pass

  app = App(master=tk.Tk(), languages=languages, configs=configs)
  app.mainloop()
  # save configs on exit
  configs = app.configs()
  with open('data/configs.json', 'w') as f: json.dump(configs, f, indent=2)
  return

if '__main__' == __name__:
  main()