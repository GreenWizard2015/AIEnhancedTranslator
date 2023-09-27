import os, json
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

    self._translateShallow = LLMChain(
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
    self._translateDeep = LLMChain(
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
    tmp = [tuple(y.strip('\n" \t\r\'{}') for y in x.split(':', maxsplit=1)) for x in tmp]
    # remove empty parts
    tmp = [x for x in tmp if (len(x) == 2) and (len(x[0]) > 0) and (len(x[1]) > 0)]
    return {k: v for k, v in tmp}
  
  def _executePrompt(self, prompt, variables):
    res = prompt.run(variables)
    logging.info(res)
    res = self._extractParts(res)
    logging.info(json.dumps(res, indent=2))
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
  
  def translate(self, text, fastTranslation, language):
    # run shallow translation
    res = self._executePrompt(
      self._translateShallow,
      {
        'UserInput': text,
        'FastTranslation': fastTranslation,
        'Language': language
      }
    )
    flags = res['Flags']
    totalIssues = sum([int(v) for k, v in flags.items()])
    if totalIssues < 2:
      yield res['Translation']
      return # all ok, no need to run deep translation
    yield res['Translation'] + '\n\n\n' + res.get('Notification', '')

    # run deep translation
    res = self._executePrompt(
      self._translateDeep,
      {
        'UserInput': text,
        'FastTranslation': res['Translation'], # use shallow translation as reference
        'Language': language,
        'InputLanguage': res.get('Input language', 'unknown'),
        'Flags': ', '.join([k for k, v in flags.items() if v])
      }
    )
    yield res['Translation']
    return