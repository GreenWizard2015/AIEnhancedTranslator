import threading

class CWorker(threading.Thread):
  def __init__(self, events):
    super().__init__(daemon=True)
    self._events = events
    self._forceTranslateEvent = threading.Event()
    return
  
  def run(self):
    oldText = None
    while True:
      isForceTranslate = self._forceTranslateEvent.wait(5)
      if isForceTranslate:
        self._forceTranslateEvent.clear()

      text = self._events.text()
      if (text == oldText) and (not isForceTranslate): continue # Not changed

      try:
        self._performTranslate(text, force=isForceTranslate)
      except Exception as e:
        print(e)
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
    except Exception as e:
      self._events.error(e)
    finally:
      self._events.endTranslate()
    return
  
  def _fastTranslate(self, text):
    return "Fast translation: " + text + "\n"
  
  def _fullTranslate(self, text, fastTranslation=None):
    return "Full translation: " + text + "\n"