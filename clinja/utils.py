import re
import sys
import click
from typing import Any
from typing import Callable
from ast import literal_eval
from functools import wraps
from functools import partial
from functools import update_wrapper


def partial_wrap(func: Callable, *args, **kwargs) -> Callable:
    """partial and update_wrapper.

    Parameters:
    -----------
    func:
        Function on which to run partial.

    Returns:
    --------
    function:
        partialed and updated function.
    """
    return update_wrapper(partial(func, *args, **kwargs), func)


def err_exit(msg: str, exit_code: int=1):
    """Echo a msg then exits.

    Parameters:
    -----------
    msg:
        Error message.
    exit_code: optional
        Numeric exit code. Exits if different than 0.
    """
    click.echo(click.style("Error: ", bold=True, fg='red') +
               click.style(msg, fg='red'), err=True)
    if exit_code != 0:
        sys.exit(exit_code)


def literal_eval_or_string(value: str) -> Any:
    """Tries to eval a string. if it fails return the string.

    Parameters:
    -----------
    value:
        String to eval.

    Returns:
    --------
        Evaled string, or the string itself.
    """
    try:
        return literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def sanitize_variable_name(variable_name:str) -> str:
    variable_name = variable_name.strip()
    if variable_name.isidentifier():
        return variable_name
    else:
        raise ValueError(f'"{variable_name}" is not a valid variable name.')


def f_docstring(docstring: str) -> Callable:
    """Bypass for f formatted docstrings.
    """
    def decorator_doc(func: Callable) -> Callable:

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__doc__ = docstring
        return wrapper
    return decorator_doc


def bold(string: str) -> str:
    """Make string bold.
    """
    return click.style(string, bold=True)


class AliasedGroup(click.Group):
    """Command aliases.
    """

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if all([l in x for l in cmd_name])]  # x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))
