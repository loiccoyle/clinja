import os
import sys
from ast import literal_eval
from functools import partial, update_wrapper, wraps
from io import TextIOWrapper
from typing import Any, Callable, Optional

import click
from jinja2 import Template
from jinja2.meta import find_undeclared_variables


def partial_wrap(func: Callable, *args, **kwargs) -> Callable:
    """partial and update_wrapper.

    Args:
        func: Function on which to run partial.

    Returns:
        partialed and updated function.
    """
    return update_wrapper(partial(func, *args, **kwargs), func)


def err_exit(msg: str, exit_code: int = 1):
    """Echo a msg then exits.

    Args:
        msg: Error message.
        exit_code: Numeric exit code. Exits if different than 0.
    """
    click.echo(
        click.style("Error: ", bold=True, fg="red") + click.style(msg, fg="red"),
        err=True,
    )
    if exit_code != 0:
        sys.exit(exit_code)


def literal_eval_or_string(value: str) -> Any:
    """Tries to eval a string. if it fails return the string.

    Args:
        value: String to eval.

    Returns:
        Evaled string, or the string itself.
    """
    try:
        return literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def sanitize_variable_name(variable_name: str) -> str:
    variable_name = variable_name.strip()
    if variable_name.isidentifier():
        return variable_name
    else:
        raise ValueError(f'"{variable_name}" is not a valid variable name.')


def f_docstring(docstring: str) -> Callable:
    """Bypass for f formatted docstrings."""

    def decorator_doc(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__doc__ = docstring
        return wrapper

    return decorator_doc


def bold(string: str) -> str:
    """Make string bold."""
    return click.style(string, bold=True)


def prompt_tty(
    string: str,
    default: Optional[str],
    show_default: bool = True,
    prompt_suffix: str = ": ",
    value_proc: Optional[Callable] = None,
) -> str:
    tty = os.open("/dev/tty", os.O_RDONLY)
    prompt_str = string
    if default and show_default:
        prompt_str += f" [{default}]"
    prompt_str += prompt_suffix
    click.echo(prompt_str, err=True, nl=False)

    user_input = ""
    while True:
        raw = os.read(tty, 1).decode("utf8")
        if not raw or raw == "\n":  # Wait for Ctrl-D or empty line
            break
        user_input += raw

    os.close(tty)
    if not user_input and default is not None:
        return default
    if value_proc is not None:
        return value_proc(user_input)
    return user_input


class AliasedGroup(click.Group):
    """Command aliases."""

    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [
            x for x in self.list_commands(ctx) if all([l in x for l in cmd_name])
        ]  # x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail("Too many matches: %s" % ", ".join(sorted(matches)))


class Template(Template):
    """Small wrapper to cleanly provide the template in the form of a
    TextIOWrapper object.
    """

    def __new__(cls, template: TextIOWrapper, *args, **kwargs):
        """
        Args:
            template: Template TextIOWrapper object.

        Attributes:
            contents: Contents of the template

        """
        contents = template.read()
        template_cls = super().__new__(cls, contents, *args, **kwargs)
        template_cls._contents = contents
        return template_cls

    def get_vars(self) -> set:
        """Gets the variables in the template.

        Returns:
            Set containing the undeclared variables found in the template.
        """
        ast = self.environment.parse(self._contents)
        return find_undeclared_variables(ast)
