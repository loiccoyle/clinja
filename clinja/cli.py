import click

from .clinja import ClinjaConfig
from .clinja import ClinjaStore
from .clinja import ClinjaTemplate
from .utils import partial_wrap
from .utils import prompt
from .utils import dict_key_diff
from .utils import err_exit
from .settings import CONF_DIR
from .settings import CONF_FILE
from .settings import STORE_FILE
from .settings import CONF_FILE_INIT
from .settings import STORE_FILE_INIT


@click.group()  # (invoke_without_command=True)
@click.pass_context
def cli(ctx):
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    if not CONF_DIR.is_dir():
        CONF_DIR.mkdir(parents=True)
    if not CONF_FILE.is_file():
        with open(CONF_FILE, 'w') as fp:
            fp.write(CONF_FILE_INIT)
    if not STORE_FILE.is_file():
        with open(STORE_FILE, 'w') as fp:
            fp.write(STORE_FILE_INIT)

    store = ClinjaStore(store=STORE_FILE)
    config = ClinjaConfig(config=CONF_FILE)
    ctx.obj['store'] = store
    ctx.obj['config'] = config


@cli.command(name='run', help='Run jinja2 on a template.')
@click.argument('template', default='-', type=click.File('r'))
@click.argument('destination', default='-', type=click.File('w'))
@click.option('--prompt', 'prompt',
              type=click.Choice(['always', 'missing', 'never']),
              default='always',
              help='When to prompt for variable values.')
@click.pass_context
def run(ctx, template, destination, prompt='always'):
    clinja_template = ClinjaTemplate(template)
    stored_vars = ctx.obj['store'].stored
    config_vars = ctx.obj['config'].run(stored=stored_vars,
                                        template=template,
                                        destination=destination)
    updated_vars = dict_key_diff(stored_vars, config_vars)
    template_vars = clinja_template.get_vars()
    missing_vars = template_vars - set(config_vars.keys())

    if prompt == 'always':
        prompt_vars = template_vars
    elif prompt == 'missing':
        prompt_vars = missing_vars
    elif prompt == 'never':
        if len(missing_vars) > 0:
           err_exit(f"Missing {', '.join(map(repr, missing_vars))}.")
        prompt_vars = {}

    for var in sorted(prompt_vars):
        default = config_vars.get(var, None)
        value = click.prompt(click.style(f"{var}", bold=True),
                             default=default,
                             type=click.STRING,
                             show_default=True)
        config_vars[var] = value
        if var != default and var not in updated_vars:
            if var in stored_vars:
                msg = ''.join(["Do you want to overwrite ",
                               click.style(stored_vars[var], bold=True),
                               " with ",
                               click.style(value, bold=True),
                               "?"])
                force = click.confirm(msg)
            else:
                force = False

            ctx.obj['store'].add(var, value, force=store)

    destination.write(clinja_template.render(config_vars))


@cli.command(name='list', help='List stored variable name/values.')
@click.pass_context
def list(ctx):
    ctx.obj['store'].list()


@cli.command(name='remove', help='Remove a stored variable name/value.')
@click.argument('variable_name', nargs=-1, type=click.STRING)
@click.pass_context
def remove(ctx, variable_name):
    for v_name in variable_name:
        try:
            ctx.obj['store'].remove((v_name))
        except KeyError as e:
            click.secho(f'Variable name {e} is not in storage.',
                    err=True,
                    bold=True,
                    fg='red')


@cli.command(name='add', help='Add a variable name/value.')
@click.argument('variable_name',
        default="",
        type=partial_wrap(prompt,
                          prompt_on='',
                          prompt_text='variable_name',
                          type=click.STRING))
@click.argument('value',
        default="",
        type=partial_wrap(prompt,
                          prompt_on='',
                          prompt_text='value',
                          type=click.STRING))
@click.option('-f', '--force', 'force', is_flag=True)
@click.pass_context
def add(ctx, variable_name: str, value: str, force: bool=False):
    """Add a variable_name/value pair to the storage.
    """
    try:
        ctx.obj['store'].add(variable_name, value, force=force)
    except ValueError:
        err_exit(f"\"{variable_name}\" already in store, use -f to overwrite.")


@cli.command(name='config', help=(f'Run clinja config file: {CONF_FILE}'
                                  " and print the variable names and values."))
@click.argument('template', default='-', type=click.File('r'))
@click.argument('destination', default='-', type=click.File('w'))
@click.pass_context
def config(ctx, template, destination):
    stored_vars = ctx.obj['store'].stored
    config_vars = ctx.obj['config'].run(stored_vars,
                                        template,
                                        destination)
    updated_vars = dict_key_diff(stored_vars, config_vars)
    for k in sorted(updated_vars):
        click.echo(f"{click.style(k, bold=True)}: {config_vars[k]}")


