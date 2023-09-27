import threading
from googletrans import Translator
import time
from .CAIAssistant import CAIAssistant

class CWorker(threading.Thread):
  def __init__(self, events):
    super().__init__(daemon=True)
    self._events = events
    self._forceTranslateEvent = threading.Event()
    self._translatorFast = Translator(service_urls=['translate.google.com'])
    self._assistant = CAIAssistant()
    return
  
  def run(self):
    oldText = None
    oldLanguage = {'code': ''}
    lastTextUpdateTime = 0
    minTextUpdateTime = 3.0 # seconds
    while True:
      isForceTranslate = self._forceTranslateEvent.wait(5)
      self._forceTranslateEvent.clear()

      text, language = self._events.userInput()
      isForceTranslate = isForceTranslate or (language['code'] != oldLanguage['code'])
      T = time.time()
      if not isForceTranslate:
        if text == oldText: continue # Not changed
        if T < lastTextUpdateTime + minTextUpdateTime: continue # Too fast
        pass
      lastTextUpdateTime = T
      oldText = text
      oldLanguage = dict(language)
      
      try:
        self._performTranslate(text, force=isForceTranslate, language=language)
      except Exception as e:
        self._events.error(e)
      continue
    return
  
  def forceTranslate(self):
    self._forceTranslateEvent.set()
    return
  
  def _performTranslate(self, text, force, language):
    text = text.strip()
    try:
      self._events.startTranslate(force)
      fastText = self._fastTranslate(text, language=language)
      self._events.fastTranslated(fastText)
      if not force: return

      for fullText in self._fullTranslate(text, fastTranslation=fastText, language=language):
        self._events.fullTranslated(fullText)
        if self._forceTranslateEvent.is_set(): break # stop if force another translate
        continue
    finally:
      self._events.endTranslate()
    return
  
  def _fastTranslate(self, text, language):
    if 0 == len(text): return ""
    translated = self._translatorFast.translate(text, dest=language['code'])
    return translated.text
  
  def _fullTranslate(self, text, fastTranslation, language):
    if 0 == len(text):
      yield ""
      return
    
    translationProcess = self._assistant.translate(
      text,
      fastTranslation=fastTranslation,
      language=language['name']
    )
    for translatedText in translationProcess:
      yield translatedText
      continue
    return