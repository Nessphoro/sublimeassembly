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
