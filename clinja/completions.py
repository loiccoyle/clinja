from pathlib import Path

from click._bashcomplete import get_completion_script

from .clinja import ClinjaStatic
from .settings import STATIC_FILE


def get_completions(shell: str='bash') -> str:
    return get_completion_script('clinja', '_CLINJA_COMPLETE', shell)


def variable_names(ctx, args, incomplete, static_file=STATIC_FILE):
    static = ClinjaStatic(static_file=static_file)
    return [k for k in static.stored.keys() if incomplete in k and k not in args[1:]]


def file_names(ctx, args, incomplete):
    # cwd = Path.cwd()
    return [p.name for p in Path().glob(incomplete + '*')]


def variable_value(ctx, args, incomplete, static_file=STATIC_FILE):
    static = ClinjaStatic(static_file=static_file)
    variable_name = args[-1]
    if len(args) == 2 and variable_name in static.stored.keys():
        return [static.stored[variable_name]]
    else:
        return []
