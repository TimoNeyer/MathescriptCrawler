import requests
from bs4 import BeautifulSoup
import os

from utils import TAGS, koetzing_config, command_to_package, latex_header, latex_footer


def convert(url:str, filename:str) -> None:
  g = Getter(url)
  le = LatexEngine(g.latex) 
  w = Writer(filename, le.content)
  w.write()

class Getter:
  def __init__(self, url:str):
    response = requests.get(url)
    response.raise_for_status()
    self.latex:str = str()
    self.html = response.content.decode('utf-8')
    self.process()

  def process(self):
    for element in BeautifulSoup(self.html, 'html.parser').find_all(True):
      if element.name in [f'h{i}' for i in range(1, 7)]:
        self.latex += f"{'\\section{' if element.name[1] == '1' else '\\subsection{'}{element.get_text(strip=True)}{'}'}\n\n"
      elif element.name == 'div':
        if element.get("class") and element.get("class")[0] in TAGS:
          self.latex += f"%% content type {element.get('class')}\n{element.get_text(strip=True)}\n\n"

class Writer:
  def __init__(self, filename:str, content:str):
    self.content = content
    self.filename = filename
    
  def write(self, *, header:str="", footer:str="", quiet:bool=False):
    if os.path.exists(self.filename) and not quiet:
      raise FileExistsError(f"File {self.filename} exists")
    if header:
      self.content = header + self.content
    if footer:
      self.content += footer
    with open(self.filename, 'w') as file:
      file.write(self.content)

class LatexEngine:
  def __init__(self, content):
    self.content = "\\begin{document}\n" + content + "\n\\end{document}"
    self.format()

  def auto_import(self):
    definitions:str = "%% commands\n"
    for k,v in koetzing_config.items():
      definitions += f"\\newcommand{{{k}}}{{{v}}}\n"
    definitions += '\n\n'
    self.content = definitions + self.content
    imports:set = set()
    for k, v in command_to_package.items():
      if self.content.find(k) != -1:
        imports.add(v)
    importstr: str = "%% autoimports\n"
    for imp in imports:
      importstr += f"\\usepackage{{{imp}}}\n" if imp else ""
    importstr += '\n\n'
    self.content = importstr + self.content

  def format(self):
    self.auto_import()
    self.content = latex_header + self.content + latex_footer