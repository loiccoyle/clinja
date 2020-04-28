import sys
import click
from typing import Any
from typing import Callable
from ast import literal_eval
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


def prompt(value: Any, prompt_on: str, prompt_text: str, type: Callable) -> Any:
    """Prompt when value equals `prompt_on`.

    Parameters:
    -----------
    value:
        Provided value.
    prompt_on:
        Prompts when equal to `value`.
    prompt_text:
        Prompt text.
    type:
        Expected type.

    Returns:
    --------
    `type`:
        Either `value` or the user's input cast as `type`.
    """
    if value is prompt_on:
        return type(click.prompt(click.style(prompt_text, bold=True)))
    else:
        return type(value)


def err_exit(msg: str, exit_code: int=1):
    """Echos a msg then exits.

    Parameters:
    -----------
    msg:
        Error message.
    exit_code:
        Numeric exit code. Exits if different than 0.
    """
    click.echo(click.style("Error: ", bold=True, fg='red') +
               click.style(msg, fg='red'), err=True)
    if exit_code != 0:
        sys.exit(exit_code)


def literal_eval_or_string(value):
    try:
        return literal_eval(value)
    except (ValueError, SyntaxError):
        return value
