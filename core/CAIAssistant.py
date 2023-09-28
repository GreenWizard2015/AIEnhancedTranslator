import os, json, re
import logging
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (ChatPromptTemplate, HumanMessagePromptTemplate)
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class CAIAssistant:
  def __init__(self, promptsFolder=None):
    if promptsFolder is None:
      promptsFolder = os.path.join(os.path.dirname(__file__), '../prompts')
    self._LLM = ChatOpenAI(model="gpt-3.5-turbo")

    self._translateShallowQuery = LLMChain(
      llm=self._LLM,
      prompt=ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate(
          prompt=PromptTemplate.from_file(
            os.path.join(promptsFolder, 'translate_shallow.txt'),
            input_variables=['UserInput', 'FastTranslation', 'Language']
          )
        ),
      ]),
    )
    self._translateDeepQuery = LLMChain(
      llm=self._LLM,
      prompt=ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate(
          prompt=PromptTemplate.from_file(
            os.path.join(promptsFolder, 'translate_deep.txt'),
            input_variables=['UserInput', 'FastTranslation', 'Language', 'Flags', 'InputLanguage']
          )
        ),
      ]),
    )
    return
  
  def _extractParts(self, text):
    text = '\n' + text + '\n' # hack to make it work
    tmp = [x for x in text.split('\n@')]
    # split into parts by :
    tmp = [tuple(y.strip('\n" \t\r\'`{}') for y in x.split(':', maxsplit=1)) for x in tmp]
    # remove empty parts
    tmp = [x for x in tmp if (len(x) == 2) and (len(x[0]) > 0) and (len(x[1]) > 0)]
    return {k: v for k, v in tmp}
  
  def _executePrompt(self, prompt, variables):
    rawPrompt = prompt.prompt.format_prompt(**variables).to_string()
    logging.info('Raw prompt: ' + rawPrompt)
    res = prompt.run(variables)
    logging.info('Raw result: ' + res)
    res = self._extractParts(res)
    logging.info('Extracted result: ' + json.dumps(res, indent=2))
    flags = {
      k: v.lower() == 'yes'
      for k, v in res.items()
      if v.lower() in ['yes', 'no']
    }
    # remove flags from result
    res = {k: v for k, v in res.items() if k not in flags}
    # add flags as separate variable
    res['Flags'] = flags
    return res
  
  def _translateShallow(self, text, translation, language):
    res = self._executePrompt(
      self._translateShallowQuery,
      {
        'UserInput': text,
        'FastTranslation': translation,
        'Language': language
      }
    )
    translation = res['Translation']
    flags = res['Flags']
    totalIssues = sum([int(v) for v in flags.values()])
    done = (totalIssues < 2)
    return res, translation, done
  
  def _translateDeep(self, text, translation, language, inputLanguage, flags):
    # extract first word from input language, can be separated by space, comma, etc.,
    inputLanguage = re.split(r'[\s,]+', inputLanguage)[0]
    inputLanguage = inputLanguage.strip().capitalize()

    res = self._executePrompt(
      self._translateDeepQuery,
      {
        'UserInput': text,
        'FastTranslation': translation,
        'Language': language,
        'InputLanguage': inputLanguage,
        'Flags': ', '.join([k for k, v in flags.items() if v])
      }
    )
    return res['Translation']
  
  def translate(self, text, fastTranslation, language):
    # run shallow translation
    raw, translation, done = self._translateShallow(
      text=text, translation=fastTranslation, language=language
    )
    yield translation, not done
    if done: return
    # run deep translation
    yield self._translateDeep(
      text=text, translation=translation, language=language,
      inputLanguage=raw.get('Input language', 'unknown'),
      flags=raw['Flags']
    ), False # no more pending translations
    return