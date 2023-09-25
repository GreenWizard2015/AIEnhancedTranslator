'''
  simple tkinter app with an input text box
  each 5 seconds thread will check if the input text box is changed
  if changed, it will process the input text and show the result in the output text box
  if user press ctrl+enter, it will force to process the input text and show the results in several output text boxes, per processing stage
'''
import tkinter as tk
import tkinter.scrolledtext as tkst
from core.worker import CWorker

class App(tk.Frame):
  def __init__(self, master=None):
    super().__init__(master)
    self._master = master
    # set global font
    self._master.option_add("*Font", ("Arial", 16))
    self._master.title("AI Enhanced Translator")
    self._UI_init()
    self.pack()
    
    self._worker = CWorker(self)
    self._worker.start()
    return

  def _UI_inputArea(self, owner):
    label = tk.Label(owner, text="Input Text:", justify="left", anchor="w")
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
  
  def _UI_outputArea(self, owner):
    # fast translation
    label = tk.Label(owner, text=self.UITextFor("Fast Translation:"), justify="left", anchor="w")
    label.pack(side="top", fill=tk.X)

    self._fastOutputText = tkst.ScrolledText(owner)
    self._fastOutputText.pack(side="top", fill=tk.BOTH, expand=tk.YES)

    # full translation
    label = tk.Label(owner, text=self.UITextFor("Full Translation:"), justify="left", anchor="w")
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
    return
  
  # events for worker
  def text(self): return self._inputText.get("1.0", tk.END)

  def startTranslate(self, force=False):
    # set output text to "Processing..."
    if force:
      self._fullOutputText.delete("1.0", tk.END)
      self._fullOutputText.insert(tk.END, self.UITextFor("Processing..."))
    return
  
  def fastTranslated(self, text):
    self._fastOutputText.delete("1.0", tk.END)
    self._fastOutputText.insert(tk.END, text)
    return
  
  def fullTranslated(self, text):
    self._fullOutputText.delete("1.0", tk.END)
    self._fullOutputText.insert(tk.END, text)
    return
  
  def error(self, e):
    self._fastOutputText.delete("1.0", tk.END)
    self._fullOutputText.insert(tk.END, "Error: " + str(e) + "\n")
    return
  
  def endTranslate(self):
    return
  
  # TODO: language selection
  def language(self): return {'code': 'sk', 'name': 'Slovak'}
  
if '__main__' == __name__:
  root = tk.Tk()
  app = App(master=root)
  app.mainloop()