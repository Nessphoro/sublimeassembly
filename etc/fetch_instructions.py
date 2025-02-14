#! /usr/bin/env python3

from dataclasses import dataclass
import sys
import time
import anthropic
import json
import xml.etree.ElementTree as ET
import re

@dataclass
class Instruction:
    mnemonic: str
    brief: str
    description: str

description_pattern = re.compile(r"<description>(.*)</description>", re.MULTILINE | re.DOTALL)

def parse_instruction_page(response):
    """Parse a response and return its data."""

    if response.stop_reason != "stop_sequence":
        print("Unexpected stop reason:", response.stop_reason)
        return None
    
    if len(response.content) != 1:
        print("Unexpected content:", response.content)
        return None

    # This is all very cursed, but sometimes the response is not per se valid XML.
    # Usually this is in the description which we'll just rip out
    # But sometimes the instruction mnemonic is is also weird, but the only case I've seen is
    # because of the ampersand so replace that.
    xml_result = "<output>\n<instruction mnemonic" + response.content[0].text + "</output>"
    description = description_pattern.search(xml_result)
    if description:
        description = description.group(1)
    else:
        print("No description found")
        print(xml_result)
        exit(1)
    
    xml_result = description_pattern.sub("", xml_result).replace("&", "&amp;")

    try:
        root = ET.fromstring(xml_result)
    except ET.ParseError as e:
        print(e)
        print(xml_result)
        exit(1)

    instructions = []
    for child in root:
        if child.tag == "instruction":
            instructions.append((child.attrib["mnemonic"], child.attrib["brief"]))
        else:
            print("Unexpected child:", child)

    for instruction in instructions:
        yield Instruction(instruction[0], instruction[1], description)

def fetch_all_instructions(bulkId):
    client = anthropic.Anthropic()
    response = client.messages.batches.retrieve(message_batch_id=bulkId)
    while response.processing_status == "in_progress":
        time.sleep(5)
        response = client.messages.batches.retrieve(message_batch_id=bulkId)
        print(response)

    instructions_dict = {}
    for result in client.messages.batches.results(bulkId):
        if result.result.type != "succeeded":
            print(result.result)
            continue
        for instruction in parse_instruction_page(result.result.message):
            if instruction.mnemonic in instructions_dict:
                print("Duplicate instruction:", instruction.mnemonic)
                continue
            instructions_dict[instruction.mnemonic] = instruction

    return instructions_dict


def main(bulkId):
    instructions_dict = fetch_all_instructions(bulkId)
    instructions = [{"Name": instruction.mnemonic, "Brief": instruction.brief, "Description": instruction.description, "Alias": []} for instruction in instructions_dict.values()]
    
    # Save to JSON file
    with open('instructions.json', 'w', encoding='utf-8') as f:
        json.dump(instructions, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(instructions)} instructions to instructions.json")

if __name__ == "__main__":
    main(sys.argv[1])