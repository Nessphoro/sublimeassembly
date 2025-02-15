import sublime

global instruction_set
global support_set
instruction_set = {}
support_set = {}


def is_asm(view):
    if view is None:
        return False

    try:
        location = view.sel()[0].begin()
    except IndexError:
        return False
    return view.match_selector(location, "source.assembly")


def is_instruction(str):
    return str.strip().upper() in instruction_set


def is_support(str):
    return len({x for x in support_set if x.casefold() == str.strip().casefold()}) > 1


def is_name(point, view):
    scopeScores = []
    scopeScores.append((view.score_selector(point, "keyword.control.assembly"),"keyword.control.assembly"))
    scopeScores.append((view.score_selector(point, "support.function.directive.assembly"),"support.function.directive.assembly"))
    scopeScores.append((view.score_selector(point, "entity.name.function.assembly"),"entity.name.function.assembly"))
    scopeScores.sort(key=lambda x: x[0])
    if(scopeScores[-1][0] > 0 and scopeScores[-1][1]  == "entity.name.function.assembly"):
        return True
    return False

def is_instruction_name(point, view):
    scopeScores = []
    scopeScores.append((view.score_selector(point, "keyword.control.assembly"),"keyword.control.assembly"))
    scopeScores.append((view.score_selector(point, "support.function.directive.assembly"),"support.function.directive.assembly"))
    scopeScores.append((view.score_selector(point, "entity.name.function.assembly"),"entity.name.function.assembly"))
    scopeScores.sort(key=lambda x: x[0])
    if(scopeScores[-1][0] > 0 and scopeScores[-1][1]  == "keyword.control.assembly"):
        return True
    return False

def printDocPanel(view, instruction, location=-1):
        html = """
            <body id=show-scope>
                <style>
                    h1 {
                        font-size: 1.1rem;
                        font-weight: 500;
                        margin: 0 0 0.5em 0;
                        font-family: system;
                    }
                    p {
                        margin-top: 0;
                        font-family: system;
                    }
                </style>
                <h1>%s</h1>
                <h2>%s</h2>
                <p>%s</p>
            </body>
        """ % (instruction["Name"], instruction["Brief"], instruction["Description"].replace("\n", "<br>"))
        view.show_popup(html, max_width=400, max_height=300, location=location, flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY)