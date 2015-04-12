from .code import *
import sublime
import sublime_plugin
import json
import os
import sys


if sys.version_info < (3, 3):
    raise RuntimeError('NASM Syntax works with Sublime Text 3 only')

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

    json_data = open(os.path.join(os.path.dirname(__file__), 'support.json'), encoding='utf-8-sig')
    data = json.load(json_data)
    json_data.close()
    for support in data:
        support_set[support["Name"]] = support
        if "Alias" in support:
            for alias in support["Alias"]:

                support_set[alias.format(support["Name"])] = instruction
    print("Loaded support set")
