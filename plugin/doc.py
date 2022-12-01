import sublime
import sublime_plugin
from .helpers import *


class AssemblyDocCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        selectedLine = self.view.line(self.view.sel()[0].begin())
        selectedLine = str(self.view.substr(selectedLine)).strip()
        splitLine = selectedLine.split(' ', maxsplit=1)
        instruction = splitLine[0]
        self.printPanel(edit, instruction_set[instruction.upper()])

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

    def printPanel(self, edit, instruction):
        doc_panel = self.view.window().create_output_panel(
            'assembly_documentation'
        )
        doc_panel.set_read_only(False)
        region = sublime.Region(0, doc_panel.size())
        doc_panel.erase(edit, region)
        doc_panel.insert(edit, 0, instruction["Name"] + " -- " + instruction["Brief"]+"\n\n"+instruction["Description"])
        self.documentation = None
        doc_panel.set_read_only(True)
        doc_panel.show(0)
        self.view.window().run_command(
            'show_panel', {'panel': 'output.assembly_documentation'}
        )
        doc_panel.settings().set("word_wrap", True)
        doc_panel.settings().set("word_wrap_column", 90)