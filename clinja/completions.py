from .clinja import ClinjaStatic
from .settings import STATIC_FILE


def variable_names(ctx, args, incomplete):
    static = ClinjaStatic(static_file=STATIC_FILE)
    return [k for k in static.stored.keys() if incomplete in k and k not in args[1:]]
