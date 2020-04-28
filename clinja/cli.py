import sys
import click

from .clinja import ClinjaDynamic
from .clinja import ClinjaStatic
from .clinja import ClinjaTemplate
from .utils import partial_wrap
from .utils import prompt
from .utils import err_exit
from .utils import literal_eval_or_string
from .settings import CONF_DIR
from .settings import DYNAMIC_FILE
from .settings import STATIC_FILE
from .settings import DYNAMIC_FILE_INIT
from .settings import STATIC_FILE_INIT
from .completions import variable_names


@click.group()  # (invoke_without_command=True)
@click.pass_context
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

    static = ClinjaStatic(static_file=STATIC_FILE)
    dynamic = ClinjaDynamic(dynamic_file=DYNAMIC_FILE)
    ctx.obj['static'] = static
    ctx.obj['dynamic'] = dynamic


@cli.command(name='run', help='Run jinja2 on a template.')
@click.argument('template', default='-', type=click.File('r'))
@click.argument('destination', default='-', type=click.File('w'))
@click.option('--prompt', 'prompt',
              type=click.Choice(['always', 'missing', 'never']),
              default='always',
              help='When to prompt for variable values.')
@click.option('-d', '--dry-run', 'dry_run', is_flag=True, default=False,
              help='Dry run, won\'t write any files or change static values.')
@click.pass_context
def run(ctx, template, destination, prompt='always', dry_run=False):
    clinja_template = ClinjaTemplate(template)
    static = ctx.obj['static']
    static_vars = static.stored
    dynamic_vars = ctx.obj['dynamic'].run(static=static_vars,
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
        value = click.prompt(click.style(f"{var}", bold=True),
                             default=default,
                             # type=click.STRING,
                             show_default=True)
        all_vars[var] = literal_eval_or_string(value)
        if not dry_run and var not in dynamic_vars.keys():
            # call the add method without cli
            add.callback(var, [value], force=False)

    if not dry_run or destination.name == '<stdout>':
        destination.write(clinja_template.render(all_vars))


@cli.command(name='list', help='List stored static variable(s).')
@click.pass_context
def list(ctx):
    ctx.obj['static'].list()


@cli.command(name='remove', help='Remove stored static variable(s).')
@click.argument('variable_name', autocompletion=variable_names, nargs=-1,
                type=click.STRING)
@click.pass_context
def remove(ctx, variable_name):
    err = False
    for v_name in variable_name:
        try:
            ctx.obj['static'].remove((v_name))
        except KeyError as e:
            err = True
            err_exit(f'Variable name {e} is not in storage.', exit_code=0)
    if exit:
        sys.exit(1)


@cli.command(name='add', help='Add a variable to static storage.')
@click.argument('variable_name',
        default="",
        type=partial_wrap(prompt,
                          prompt_on='',
                          prompt_text='variable name',
                          type=click.STRING))
@click.argument('value', nargs=-1, type=click.STRING)
@click.option('-f', '--force', 'force', is_flag=True, default=False)
@click.pass_context
def add(ctx, variable_name: str, value: str, force: bool=False):
    """Add a variable_name/value pair to the storage.
    """
    if value == ():
        value = click.prompt(click.style("value", bold=True),
                             type=click.STRING)
    else:
        value = ' '.join(value)
    value = literal_eval_or_string(value)
    variable_name = variable_name.strip()

    static = ctx.obj['static']
    try:
        static.add(variable_name,
                   literal_eval_or_string(value),
                   force=force)
    except ValueError:
        msg = ''.join(["Do you want to overwrite ",
                       click.style(str(static.stored[variable_name]), bold=True),
                       " with ",
                       click.style(str(value), bold=True),
                       "?"])
        if click.confirm(msg):
            static.add(variable_name,
                       literal_eval_or_string(value),
                       force=True)


@cli.command(name='test', help=f'Test run your dynamic file: {DYNAMIC_FILE}')
@click.argument('template', default='-', type=click.File('r'))
@click.argument('destination', default='-', type=click.File('w'))
@click.pass_context
def test(ctx, template, destination):
    dynamic_vars = ctx.obj['dynamic'].run(static=ctx.obj['static'].stored,
                                          template=template,
                                          destination=destination)
    for k in sorted(dynamic_vars.keys()):
        click.echo(f"{click.style(k, bold=True)}: {dynamic_vars[k]}")
