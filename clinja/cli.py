import sys
import click

from typing import Any
from pathlib import Path
from json import loads
from json import JSONDecodeError

from .clinja import ClinjaDynamic
from .clinja import ClinjaStatic
from .utils import Template
from .utils import partial_wrap
from .utils import err_exit
from .utils import literal_eval_or_string
from .utils import sanitize_variable_name
from .utils import f_docstring
from .utils import bold
from .utils import AliasedGroup
from .settings import CONF_DIR
from .settings import DYNAMIC_FILE
from .settings import STATIC_FILE
from .settings import DYNAMIC_FILE_INIT
from .settings import STATIC_FILE_INIT
from .completions import get_completions
from .completions import variable_names
from .completions import variable_value
from .completions import file_names


def prompt_value_check(value):
    try:
        return literal_eval_or_string(value)
    except Exception as e:
        raise click.UsageError(str(e))


def prompt_variable_name_check(value):
    try:
        return sanitize_variable_name(value)
    except ValueError as e:
        raise click.UsageError(str(e))


@click.group(cls=AliasedGroup)
@click.pass_context
@f_docstring(f'''
A versatile jinja command line interface.

Clinja uses two sources to find values for jinja variables. A {bold('static')}
source, which is just a json file, and a {bold('dynamic')} source, which is a
python source file. Clinja populates the {bold('static')} source with user
entered values. Whereas the {bold('dynamic')} variables are computed at run time
by the python file.

In short:

    Clinja stores all {bold('static')} variables in: {bold(str(STATIC_FILE))}

    Clinja's {bold('dynamic')} variables are computed by the python file: {bold(str(DYNAMIC_FILE))}
''')
def cli(ctx):  # pragma: no cover
    ctx.ensure_object(dict)

    if not CONF_DIR.is_dir():
        CONF_DIR.mkdir(parents=True)
    if not DYNAMIC_FILE.is_file():
        with open(DYNAMIC_FILE, 'w') as fp:
            fp.write(DYNAMIC_FILE_INIT)
    if not STATIC_FILE.is_file():
        with open(STATIC_FILE, 'w') as fp:
            fp.write(STATIC_FILE_INIT)
    ctx.obj['static'] = ClinjaStatic(static_file=STATIC_FILE)
    ctx.obj['dynamic'] = ClinjaDynamic(dynamic_file=DYNAMIC_FILE)


@cli.command(name='run')
@click.argument('template', default='-', type=click.File('r'),
                autocompletion=file_names)
@click.argument('destination', default='-', type=click.File('w'),
                autocompletion=file_names)
@click.option('--prompt', 'prompt',
              type=click.Choice(['always', 'missing', 'never']),
              default='always',
              help='When to prompt for variable values.')
@click.option('-d', '--dry-run', 'dry_run', is_flag=True, default=False,
              help=('Dry run, won\'t write any files or change/add any static'
                    ' values.')
              )
@click.pass_obj
def run(obj, template, destination, prompt='always', dry_run=False):
    """Run jinja on a template.

    TEMPLATE (optional, default: stdin): template file on which to run jinja,
    if using stdin, --prompt is set to "never".

    DESTINATION (optional, default: stdout): output destination.
    """
    if template.name == '<stdin>':  # pragma: no cover
        prompt = 'never'
    clinja_template = Template(template)
    static = obj['static']
    static_vars = static.stored
    dynamic_vars = obj['dynamic'].run(static_vars=static_vars,
                                      template=template,
                                      destination=destination)
    all_vars = {**static_vars, **dynamic_vars}

    if prompt == 'always':
        prompt_vars = clinja_template.get_vars()
    elif prompt == 'missing' or prompt == 'never':
        prompt_vars = clinja_template.get_vars() - (set(dynamic_vars.keys()) |
                                                    set(static_vars.keys()))
        if prompt == 'never' and len(prompt_vars) > 0:
            # only continue if there are no missing vars
            err_exit(f"Missing {', '.join(map(repr, prompt_vars))}.")

    for var in sorted(prompt_vars):
        value = click.prompt(bold(var),
                             default=all_vars.get(var, None),
                             value_proc=prompt_value_check,
                             show_default=True)
        all_vars[var] = value
        if not dry_run and var not in dynamic_vars.keys():
            in_static = var in static_vars.keys()
            if (not in_static and
                click.confirm(f'Do you want to store {bold(var)}?', default=True)):
                add.callback(var, value, force=False)
            elif in_static:
                # call the add method without cli
                add.callback(var, value, force=False)

    if not dry_run or destination.name == '<stdout>':
        destination.write(clinja_template.render(all_vars))


@cli.command(name='list')
@click.argument('pattern', default="", type=click.STRING,
                autocompletion=variable_names)
@click.pass_obj
def list(obj, pattern=None):
    '''List stored static variable(s).

    PATTERN (optional): regexp pattern for variable name filtering.
    '''
    for k, v in obj['static'].list(pattern=pattern):
        click.echo(f'{bold(k)}: {v}')


@cli.command(name='remove')
@click.argument('variable_name',
                autocompletion=variable_names,
                nargs=-1,
                type=sanitize_variable_name)
@click.pass_obj
def remove(obj, variable_name):
    '''Remove stored static variable(s).
    '''
    static = obj['static']
    err = False
    for v_name in variable_name:
        try:
            static.remove(v_name)
        except KeyError as e:
            err = True
            err_exit(f'Variable name {e} is not in storage.', exit_code=0)
    if err:
        sys.exit(1)


@cli.command(name='add')
@click.argument('variable_name',
                default="",
                autocompletion=variable_names,
                type=lambda x: sanitize_variable_name(x) if x != '' else '')
@click.argument('value',
                nargs=-1,
                type=click.STRING,
                autocompletion=variable_value)
@click.option('-f', '--force', 'force', is_flag=True, default=False)
@click.pass_obj
def add(obj, variable_name: str="", value: Any=(), force: bool=False):
    """Add a variable to static storage.
    """
    static = obj['static']
    if variable_name == '':
        variable_name = click.prompt(bold('variable name'),
                                     value_proc=prompt_variable_name_check)
    if value == ():
        value = click.prompt(bold("value"),
                             value_proc=prompt_value_check)
    elif isinstance(value, tuple):
        value = ' '.join(value)
    if isinstance(value, str):
        # check for when this is called outside of command line
        value = literal_eval_or_string(value)

    try:
        static.add(variable_name, value, force=force)
    except ValueError:
        msg = ''.join(["Do you want to overwrite ",
                       bold(str(static.stored[variable_name])),
                       " with ",
                       bold(str(value)),
                       "?"])
        if click.confirm(msg, default=True):
            static.add(variable_name, value, force=True)


@cli.command(name='test')
@click.option('--template', type=Path, help='mock template path.')
@click.option('--destination', type=Path, help='mock template path.')
@click.option('--run_cwd', default=Path.cwd(), type=Path,
              help='mock current working directory path.')
@click.option('--static_vars', type=click.STRING, help='mock json format static variables.')
@click.pass_obj
def test(obj, template=None, destination=None, run_cwd=Path.cwd(), static_vars=None):
    '''Test run your dynamic.py file.

    Run your dynamic.py file using mock values.

    TEMPLATE, DESTINATION, RUN_CWD and STATIC_VARS are provided to the
    dynamic.py file in their respective variable names.
    '''
    if static_vars is not None:
        try:
            static_vars = loads(static_vars)
        except JSONDecodeError as e:
            err_exit(f'"{static_vars}" is not valid json, {e}')
    else:
        static_vars = obj['static'].stored
    dynamic_vars = obj['dynamic'].run(static_vars=static_vars,
                                      template=template,
                                      destination=destination,
                                      run_cwd=run_cwd)
    for k, v in sorted(dynamic_vars.items()):
        click.echo(f"{bold(k)}: {v}")

@cli.command(name='completion')
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish']))
def completion(shell):
    '''Generate autocompletion for your shell.
    '''
    click.echo(get_completions(shell))
