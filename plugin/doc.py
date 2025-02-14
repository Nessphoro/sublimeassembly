import sublime
import sublime_plugin
from .helpers import *


class AssemblyDocCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        selectedLine = self.view.line(self.view.sel()[0].begin())
        selectedLine = str(self.view.substr(selectedLine)).strip()
        splitLine = selectedLine.split(' ', maxsplit=1)
        instruction = splitLine[0]
        printDocPanel(self.view, instruction_set[instruction.upper()])

    def is_enabled(self):
        if not is_asm(self.view):
            return False
        try:
            selectedLine = self.view.line(self.view.sel()[0].begin())
            selectedLine = str(self.view.substr(selectedLine)).strip()
            splitLine = selectedLine.split(' ', maxsplit=1)
            instruction = splitLine[0]
        except:
            return False
        return instruction.upper() in instruction_set

    