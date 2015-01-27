import sublime
import sublime_plugin
import json
import os
import sys

instruction_set = {}

if sys.version_info < (3, 3):
    raise RuntimeError('NASM Syntax works with Sublime Text 3 only')


def is_asm(view):
    if view is None:
        return False

    try:
        location = view.sel()[0].begin()
    except IndexError:
        return False
    return view.match_selector(location, "source.assembly")


class completionListener(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        if is_asm(view):
            completions = [[instruction + " \t" + instruction_set[instruction]["Brief"], instruction.lower()]\
             for instruction in instruction_set.keys() if instruction.startswith(prefix.upper())]
            return completions

class docsCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        selectedLine = self.view.line(self.view.sel()[0].begin())
        selectedLine = str(self.view.substr(selectedLine))
        splitLine = selectedLine.split(' ', maxsplit=1)
        instruction = splitLine[0]
        self.printPanel(edit, instruction_set[instruction.upper()])

    def iseEnabled(self, edit):
        return is_asm(self.view)

    def printPanel(self, edit, instruction):
        doc_panel = self.view.window().create_output_panel(
            'anaconda_documentation'
        )
        doc_panel.set_read_only(False)
        region = sublime.Region(0, doc_panel.size())
        doc_panel.erase(edit, region)
        doc_panel.insert(edit, 0, instruction["Name"] + " -- " + instruction["Brief"]+"\n\n"+instruction["Description"])
        self.documentation = None
        doc_panel.set_read_only(True)
        doc_panel.show(0)
        self.view.window().run_command(
            'show_panel', {'panel': 'output.anaconda_documentation'}
        )
        doc_panel.settings().set("word_wrap", True)
        doc_panel.settings().set("word_wrap_column", 90)


def plugin_loaded():
    json_data = open(os.path.join(os.path.dirname(__file__), 'instructions.json'), encoding='utf-8-sig')
    data = json.load(json_data)
    json_data.close()
    for instruction in data:
        if instruction['Name'] in instruction_set:
            print(instruction['Name'])
        instruction_set[instruction['Name']] = instruction
        for alias in instruction["Alias"]:
            instruction_set[alias] = instruction
    print("Loaded instruction set")
