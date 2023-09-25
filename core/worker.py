import threading
from googletrans import Translator
import time

class CWorker(threading.Thread):
  def __init__(self, events):
    super().__init__(daemon=True)
    self._events = events
    self._forceTranslateEvent = threading.Event()
    self._translatorFast = Translator(service_urls=['translate.google.com'])
    return
  
  def run(self):
    oldText = None
    lastTextUpdateTime = 0
    minTextUpdateTime = 3.0 # seconds
    while True:
      isForceTranslate = self._forceTranslateEvent.wait(5)
      self._forceTranslateEvent.clear()

      text = self._events.text()
      T = time.time()
      if not isForceTranslate:
        if text == oldText: continue # Not changed
        if T < lastTextUpdateTime + minTextUpdateTime: continue # Too fast
        pass
      lastTextUpdateTime = T
      oldText = text
      
      try:
        self._performTranslate(text, force=isForceTranslate)
      except Exception as e:
        self._events.error(e)
      continue
    return
  
  def forceTranslate(self):
    self._forceTranslateEvent.set()
    return
  
  def _performTranslate(self, text, force=False):
    try:
      self._events.startTranslate(force)
      fastText = self._fastTranslate(text)
      self._events.fastTranslated(fastText)
      if not force: return

      fullText = self._fullTranslate(text, fastTranslation=fastText)
      self._events.fullTranslated(fullText)
    finally:
      self._events.endTranslate()
    return
  
  def _fastTranslate(self, text):
    if not text: return ""
    translated = self._translatorFast.translate(text, dest=self._events.language()['code'])
    return translated.text
  
  def _fullTranslate(self, text, fastTranslation=None):
    if not text: return ""
    return "Full translation: " + text + "\n"