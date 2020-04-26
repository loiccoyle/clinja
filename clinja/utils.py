import sys
import click
from typing import Any
from typing import Callable
from functools import partial
from functools import update_wrapper
from contextlib import contextmanager

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


def dict_key_diff(ori: dict, new: dict) -> set:
    """Performs the diff of 2 dictionaries.

    Parameters:
    -----------
    ori:
        Original dictionary.
    new:
        `ori` but with changed and or added key/values.

    Returns:
    --------
    set:
        Set of the added and or changed keys.
    """
    new_keys = set(new.keys())
    ori_keys = set(ori.keys())
    out = new_keys - ori_keys
    for key in ori_keys - out:
        if ori[key] != new[key]:
            out.append(key)
    return out


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
