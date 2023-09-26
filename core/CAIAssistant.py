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
            input_variables=['UserInput', 'FastTranslation', 'Language', 'Flags']
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
  
  def translate(self, text, fastTranslation, language):
    # run shallow translation
    res = self._translateShallow.run({
      'UserInput': text,
      'FastTranslation': fastTranslation,
      'Language': language
    })
    # extract translation
    translation = self._extractParts(res)
    logging.info(json.dumps(translation, indent=2))
    flags = {
      k: v.lower() == 'yes'
      for k, v in translation.items()
      if v.lower() in ['yes', 'no']
    }
    totalIssues = sum([int(v) for k, v in flags.items()])
    if totalIssues < 2:
      yield translation['Translation']
      return # all ok, no need to run deep translation
    yield translation['Translation'] + '\n\n\n' + translation.get('Notification', '')

    # run deep translation
    res = self._translateDeep.run({
      'UserInput': text,
      'FastTranslation': translation['Translation'], # use shallow translation as reference
      'Language': language,
      'Flags': ', '.join([k for k, v in flags.items() if v])
    })
    # extract final translation
    translation = self._extractParts(res)
    logging.info(json.dumps(translation, indent=2))
    yield translation['Translation']
    return