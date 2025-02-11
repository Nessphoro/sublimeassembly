#! /usr/bin/env python3

"""
This script generates the syntax file for the Assembly x86 (NASM) syntax.
It reads the template file and the instructions.json file to generate the syntax.
"""


import json

def generate_syntax(template_file, output_file):
    with open(template_file, "r") as file:
        template = file.read()

    with open("instructions.json", "r") as file:
        instructions_data = json.load(file)

    instructions = []
    for instruction in instructions_data:
        aliases = instruction.get("Alias", [])
        if not instruction["Name"].endswith("cc"):
            aliases.append(instruction["Name"].strip().lower())

        instructions.extend(map(lambda x: x.strip().lower(), aliases))

    formated = template.replace("%INSTRUCTIONS%", "|".join(instructions))

    with open(output_file, "w") as file:
        file.write(formated)


if __name__ == "__main__":
    generate_syntax("Assembly x86.tmLanguage.template", "Assembly x86.tmLanguage")
    generate_syntax("Assembly x86.JSON-tmLanguage.template", "Assembly x86.JSON-tmLanguage")
    