from click.shell_completion import BashComplete, FishComplete, ZshComplete

from .clinja import ClinjaStatic
from .settings import STATIC_FILE


def get_completions(ctx, command, shell: str = "bash"):
    completion_class_map = {
        "bash": BashComplete,
        "zsh": ZshComplete,
        "fish": FishComplete,
    }
    completion = completion_class_map[shell](command, ctx, "clinja", "_CLINJA_COMPLETE")
    return completion.source()


def variable_names(ctx, args, incomplete, static_file=STATIC_FILE):
    static = ClinjaStatic(static_file=static_file)
    return [k for k in static.stored.keys() if incomplete in k and k not in args[1:]]


def variable_value(ctx, args, incomplete, static_file=STATIC_FILE):
    static = ClinjaStatic(static_file=static_file)
    variable_name = args[-1]
    if len(args) == 2 and variable_name in static.stored.keys():
        return [static.stored[variable_name]]
    else:
        return []
