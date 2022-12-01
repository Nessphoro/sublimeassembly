import sublime
import sublime_plugin
from .helpers import *
from .context import *

class completionListener(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        if is_asm(view):
            prefixLineStart = view.line(locations[0])
            line = view.substr(prefixLineStart).strip()
            lskip = view.substr(prefixLineStart).index(line)
            splitLine = line.split(' ', maxsplit=1)  # maybe str.partition?
            if(len(splitLine) > 1):
                # The user is typing in the middle. Check if the start was a label
                if is_name(prefixLineStart.begin()+lskip, view):
                    print("Lable first")
                else:
                    # No a label start, so could be instruction or a support directive
                    print("Instuction context")
                    return self.handleInstructionContext(view, prefix, locations)
            else:
                prefix = line  # the user is just starting to type
                if prefix.startswith("%"):
                    return self.handleSupportContext(view, prefix, locations)
                else:
                    return self.handleInsturctionOpcodeContext(view, prefix, locations)

    def handleInstructionContext(self, view, prefix, locations):
        completions = [[name[0]+'\t'+name[1], name[0]] for name in contexts[view.id()].getLocals(set()) if name[0].casefold().startswith(prefix.casefold())]
        return (completions, sublime.INHIBIT_WORD_COMPLETIONS)

    def handleSupportContext(self, view, prefix, locations):
        return [[si, si] for si in support_set.keys() if si.casefold().startswith(prefix.casefold())]

    def handleInsturctionOpcodeContext(self, view, prefix, locations):
        completions= [[instruction.casefold() + " \t" + instruction_set[instruction]["Brief"], instruction.lower()]\
            for instruction in instruction_set.keys() if instruction.casefold().startswith(prefix.casefold())]
        completions.extend(self.handleSupportContext(view, prefix, locations))
        completions.sort(key=lambda x: len(x[1]))
        return (completions, sublime.INHIBIT_WORD_COMPLETIONS)
