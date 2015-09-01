import sublime
import sublime_plugin
import os.path
from time import time
from .helpers import is_name, is_asm

global contexts
contexts = dict()
processing = dict()
scanRequests = set()

class Context:

    def __init__(self, view):
        self.locals = set()
        self.includes = set()
        self.view = view
        self.mtime = 0
        self.vid = view.id()
        self._fileName = None
        contexts[self.vid] = self

    def getFileName(self):
        return self._fileName

    def setFileName(self, fname):
        if self._fileName is not None:
            del contexts[self._fileName]
        self._fileName = fname
        contexts[self._fileName] = self

    def changeView(self, view):
        del contexts[self.vid]
        self.view = view
        self.vid = view.id()
        contexts[self.vid] = self

    def checkintersction(self, sel, line):
        for l in sel:
            selectedLine = self.view.line(l)
            if selectedLine.intersects(line):
                return True
        return False

    def ensureFresh(self):
        if os.path.getmtime(self._fileName) > self.mtime:
            if self.view.file_name() is None:
                newView = sublime.active_window().find_open_file(self._fileName)
                if newView is None:
                    scanRequests.add(self._fileName)
                    sublime.active_window().open_file(self._fileName)
                else:
                    self.changeView(newView)
                    self.rescan()



    def getLocals(self, files):
        if self._fileName in files:
            return set()
        files.add(self._fileName)
        localSet = self.locals
        for include in self.includes:
            localSet = localSet.union(contexts[include].getLocals(files))

        return localSet

    def rescan(self):
        self.mtime = time()
        self.locals.clear()
        self.includes.clear()
        if self.view.file_name() is not None:
            self.setFileName(self.view.file_name())
        fileRegion = sublime.Region(0, self.view.size())
        lines = self.view.lines(fileRegion)
        for l in lines:
            if self.checkintersction(self.view.sel(), l):
                print("intersection")
                continue
            fullLine = self.view.substr(l)
            line = fullLine.strip()
            if len(line) == 0:
                continue
            split = line.split(" ", maxsplit=1)

            if split[0].casefold().startswith("%include".casefold()) and self.view.file_name() is not None:
                print("Scope extension")
                try:
                    fstart = split[1].index('"')
                    fend = split[1].rindex('"')
                    fName = split[1][fstart+1:fend]
                    fName = os.path.join(os.path.dirname(self._fileName), fName)
                    if os.path.isfile(fName):
                        if fName in contexts:
                            # Awesome, we have the file
                            print("Added to includes")
                            self.includes.add(fName)
                            contexts[fName].ensureFresh()
                        else:
                            # We have to load it
                            newView = sublime.active_window().find_open_file(fName)
                            if newView is None:
                                scanRequests.add(fName)
                                sublime.active_window().open_file(fName)
                            else:
                                newView.set_syntax_file("Packages/NASM x86 Assembly/Assembly x86.tmLanguage")
                                context = Context(newView)
                                context.rescan()
                            self.includes.add(fName)
                except:
                    pass

            # figure out how much we skipped, if any.
            lskip = fullLine.index(split[0])
            termStart = l.begin() + lskip
            if is_name(termStart, self.view):
                self.locals.add((split[0].strip(":"), "label"))
        print(self.locals)




class ContextManager(sublime_plugin.EventListener):

    def on_modified_async(self, view):
        global processing
        if not is_asm(view):
            return

        if view.id() in processing or view.file_name() in processing:
            return
        processing[view.id()] = True
        if view.file_name() is not None:
            processing[view.file_name()] = True

        def timeoutCallback():
            del processing[view.id()]
            if view.file_name() is not None:
                del processing[view.file_name()]

        sublime.set_timeout(timeoutCallback, 1000)
        if view.id() in contexts or view.file_name() in contexts:
            if view.file_name() in contexts:
                contexts[view.file_name()].changeView(view)
                contexts[view.file_name()].rescan()
            else:
                contexts[view.id()].rescan()
        else:
            context = Context(view)
            context.rescan()

    def on_load_async(self, view):
        if view.file_name() in scanRequests or view.file_name() in contexts:
            view.set_syntax_file("Packages/NASM x86 Assembly/Assembly x86.tmLanguage")
        if is_asm(view):
            if view.file_name() not in contexts:
                print("File was loaded out-of-band")
                # add the context
                processing[view.id()] = True
                processing[view.file_name()] = True
                context = Context(view)
                context.rescan()

                del processing[view.id()]
                del processing[view.file_name()]
                if view.file_name() in scanRequests:
                    scanRequests.remove(view.file_name())
                    sublime.active_window().focus_view(view)
                    sublime.active_window().run_command("close_file")  # the user probably won't like that we opened some stupid file
            elif view.file_name() in scanRequests:
                # a bit weird, but some closed file has changed and we don't know about it
                processing[view.id()] = True
                processing[view.file_name()] = True

                contexts[view.file_name()].changeView(view)
                contexts[view.file_name()].rescan()
                scanRequests.remove(view.file_name())
                sublime.active_window().focus_view(view)
                sublime.active_window().run_command("close_file")  # the user probably won't like that we opened some stupid file

                del processing[view.id()]
                del processing[view.file_name()]
