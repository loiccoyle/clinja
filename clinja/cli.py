import sys
import click

from pathlib import Path
from json import loads
from json import JSONDecodeError

from .clinja import ClinjaDynamic
from .clinja import ClinjaStatic
from .clinja import ClinjaTemplate
from .utils import partial_wrap
from .utils import prompt
from .utils import err_exit
from .utils import literal_eval_or_string
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


@click.group(cls=AliasedGroup)  # (invoke_without_command=True)
@click.pass_context
@f_docstring(f'''
A smart and hackable jinja command line interface.

Clinja has two sources for jinja variables, a {bold('static')} source, a json
file, and a {bold('dynamic')} source, a python source file. Clinja populates
the {bold('static')} source with user entered values.
Whereas the {bold('dynamic')} variables are computed at run time by the python file.

In short:

    Clinja stores all {bold('static')} variables in: {bold(str(STATIC_FILE))}

    Clinja's {bold('dynamic')} variables are computed by the python file: {bold(str(DYNAMIC_FILE))}
''')
def cli(ctx):
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
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
@click.pass_context
def run(ctx, template, destination, prompt='always', dry_run=False):
    """Run jinja on a template.

    TEMPLATE (optional, default: stdin): template file on which to run jinja.

    DESTINATION (optional, default: stdout): output destination.
    """
    clinja_template = ClinjaTemplate(template)
    static = ctx.obj['static']
    static_vars = static.stored
    dynamic_vars = ctx.obj['dynamic'].run(static_vars=static_vars,
                                          template=template,
                                          destination=destination)
    all_vars = {**static_vars, **dynamic_vars}

    if prompt == 'always':
        prompt_vars = clinja_template.get_vars()
    elif prompt == 'missing' or prompt == 'never':
        prompt_vars = clinja_template.get_vars() - set(dynamic_vars.keys() +
                                                       static_vars.keys())
        if prompt == 'never' and len(prompt_vars) > 0:
            # only continue if there are no missing vars
           err_exit(f"Missing {', '.join(map(repr, prompt_vars))}.")

    for var in sorted(prompt_vars):
        default = all_vars.get(var, None)
        value = click.prompt(bold(var),
                             default=default,
                             # type=click.STRING,
                             show_default=True)
        try:
            all_vars[var] = static.sanitize_variable_name(value)
        except ValueError as e:
            err_exit(str(e))
        if not dry_run and var not in dynamic_vars.keys():
            # call the add method without cli
            add.callback(var, value, force=False)

    if not dry_run or destination.name == '<stdout>':
        destination.write(clinja_template.render(all_vars))


@cli.command(name='list')
@click.argument('pattern', default="", type=click.STRING,
                autocompletion=variable_names)
@click.pass_context
def list(ctx, pattern=None):
    '''List stored static variable(s).

    PATTERN (optional): regexp pattern for variable name filtering.
    '''
    for k, v in ctx.obj['static'].list(pattern=pattern):
        click.echo(f'{bold(k)}: {v}')


@cli.command(name='remove')
@click.argument('variable_name', autocompletion=variable_names, nargs=-1,
                type=click.STRING)
@click.pass_context
def remove(ctx, variable_name):
    '''Remove stored static variable(s).
    '''
    static = ctx.obj['static']
    err = False
    for v_name in variable_name:
        try:
            static.remove(static.sanitize_variable_name(v_name))
        except KeyError as e:
            err = True
            err_exit(f'Variable name {e} is not in storage.', exit_code=0)
        except ValueError as e:
            err = True
            err_exit(str(e), exit_code=0)
    if exit:
        sys.exit(1)


@cli.command(name='add')
@click.argument('variable_name',
                default="",
                autocompletion=variable_names,
                type=partial_wrap(prompt,
                                  prompt_on='',
                                  prompt_text='variable name',
                                  type=click.STRING))
@click.argument('value', nargs=-1, type=click.STRING,
                autocompletion=variable_value)
@click.option('-f', '--force', 'force', is_flag=True, default=False)
@click.pass_context
def add(ctx, variable_name: str, value: str, force: bool=False):
    """Add a variable to static storage.
    """
    static = ctx.obj['static']
    if value == ():
        value = click.prompt(bold("value"),
                             type=click.STRING)
    else:
        value = ' '.join(value)
    value = literal_eval_or_string(value)

    try:
        variable_name = static.sanitize_variable_name(variable_name)
    except ValueError as e:
        err_exit(str(e))

    try:
        static.add(variable_name,
                   literal_eval_or_string(value),
                   force=force)
    except ValueError:
        msg = ''.join(["Do you want to overwrite ",
                       bold(static.stored[variable_name]),
                       " with ",
                       bold(str(value)),
                       "?"])
        if click.confirm(msg):
            static.add(variable_name,
                       literal_eval_or_string(value),
                       force=True)


@cli.command(name='test')
@click.argument('template', default='-',
                type=lambda x: Path(x).absolute() if x != '-' else None,
                autocompletion=file_names)
@click.argument('destination', default='-',
                type=lambda x: Path(x).absolute() if x != '-' else None,
                autocompletion=file_names)
@click.argument('run_cwd', default=Path.cwd().absolute(), type=Path)
@click.argument('static_vars', default='', type=click.STRING)
@click.pass_context
def test(ctx, template, destination, run_cwd=Path.cwd(), static_vars=None):
    '''Test run your dynamic.py file.

    Run your dynamic.py file using mock values for the provided variables.

    TEMPLATE, DESTINATION, RUN_CWD and STATIC_VARS are provided to the
    dynamic.py file in their respective variable names.

    TEMPLATE (optional, default: None): mock template path.

    DESTINATION (optional, default: None): mock destination path.

    RUN_CWD (optional, default: cwd): mock current working directory.

    STATIC_VARS (optional, default: static.json): mock json format static
    variables.
    '''
    if static_vars != '':
        try:
            static_vars = loads(static_vars)
        except JSONDecodeError as e:
            err_exit(f'"{static_vars}" is not valid json, {e}')
    else:
        static_vars = ctx.obj['static'].stored
    dynamic_vars = ctx.obj['dynamic'].run(static_vars=static_vars,
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
    click.echo(get_completion(shell))
