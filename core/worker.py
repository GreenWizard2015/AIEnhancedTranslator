import threading
from googletrans import Translator
import time
from functools import lru_cache
from .CAIAssistant import CAIAssistant

class CWorker(threading.Thread):
  def __init__(self, events):
    super().__init__(daemon=True)
    self._events = events
    self._forceTranslateEvent = threading.Event()
    self._translatorFast = Translator(service_urls=['translate.google.com'])
    self._assistant = CAIAssistant()

    # TODO: Fix this hack. It's not thread safe. Also check related issues with UI during refinement.
    self._refinement = None
    return
  
  def run(self):
    oldText = None
    oldLanguage = {'code': ''}
    lastTextUpdateTime = 0
    minTextUpdateTime = 3.0 # seconds
    while True:
      isForceTranslate = self._forceTranslateEvent.wait(5)
      self._forceTranslateEvent.clear()

      if self._refinement is not None:
        self._doRefine()
        continue

      userInput = self._events.userInput()
      text = userInput['text']
      language = userInput['language']

      isLanguageChanged = language['code'] != oldLanguage['code']
      if isLanguageChanged: # reload UI translation if language changed
        try:
          newLocalization = self._updateLocalization(
            languageName=language['name'], languageCode=language['code']
          )
          self._events.updateLocalization(newLocalization)
          oldText = None # reset text
          oldLanguage = dict(language)
        except Exception as e:
          self._events.error(e)
        continue
      
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
      fastText = self._fastTranslate(text, languageCode=language['code'])
      self._events.fastTranslated(fastText)
      if not force: return

      translationProcess = self._fullTranslate(text, fastTranslation=fastText, language=language)
      for translationResult in translationProcess:
        self._events.fullTranslated(translationResult)
        if self._forceTranslateEvent.is_set(): break # stop if force another translate
        continue
    finally:
      self._events.endTranslate()
    return
  
  @lru_cache(maxsize=20)
  def _fastTranslate(self, text, languageCode):
    if 0 == len(text): return ""
    translated = self._translatorFast.translate(text, dest=languageCode)
    return translated.text
  
  def _fullTranslate(self, text, fastTranslation, language):
    if 0 == len(text):
      yield "", False
      return
    
    translationProcess = self._assistant.translate(
      text, language=language['name'],
      fastTranslation=fastTranslation,
    )
    for translation in translationProcess: yield translation
    return
  
  @lru_cache(maxsize=None)
  def _updateLocalization(self, languageName, languageCode):
    strings = self._events.localizationStrings()
    res = self._translatorFast.translate('\n'.join(strings), dest=languageCode).text.split('\n')
    res = [x.strip() for x in res]
    res = [x for x in res if len(x) > 0]
    assert len(strings) == len(res)
    res = {k: v for k, v in zip(strings, res)}
    return res
  
  def bindAPI(self, key):
    self._assistant.bindAPI(key)
    return
  
  def refine(self, previousTranslation):
    self._refinement = previousTranslation
    self.forceTranslate()
    return
  
  def _doRefine(self):
    assert self._refinement is not None
    previousTranslation = self._refinement
    self._refinement = None
    try:
      res = self._assistant.refine(previousTranslation)
      self._events.fullTranslated(res)
    except Exception as e:
      self._events.error(e)
    return