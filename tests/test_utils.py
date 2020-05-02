import click
from io import TextIOWrapper
from pathlib import Path
from unittest import TestCase
from shutil import rmtree
from click.testing import CliRunner

from clinja import utils


class TestUtils(TestCase):

    def test_partial_wrap(self):
        def func_test(arg1, arg2):
            return arg1 + arg2

        partialed = utils.partial_wrap(func_test, 10)
        self.assertEqual(partialed(3), 13)
        self.assertEqual(partialed.__name__, 'func_test')

    def test_err_exit(self):
        msg = 'test'
        exit_code = 1
        with self.assertRaises(SystemExit):
            utils.err_exit(msg, exit_code=exit_code)

    def test_literal_eval_or_string(self):
        self.assertEqual(utils.literal_eval_or_string('something'), 'something')
        self.assertEqual(utils.literal_eval_or_string('["a", "b"]'), ['a', 'b'])
        self.assertEqual(utils.literal_eval_or_string('{"a":1, "b":2}'), {'a': 1, 'b':2})
        # with self.assertRaises(SyntaxError):
        #     utils.literal_eval_or_string('[1')

    def test_f_docstring(self):
        @utils.f_docstring(f'{1+1}')
        def func_test():
            return True
        self.assertEqual(func_test.__doc__, '2')
        self.assertTrue(func_test())

    def test_bold(self):
        self.assertEqual(utils.bold('bla'), '\x1b[1mbla\x1b[0m')


class TestTemplate(TestCase):
    def setUp(self):
        self.test_dir = Path('test_utils_template')
        self.test_dir.mkdir(exist_ok=True)
        self.template = self.test_dir / 'test_template'
        self.template_contents = """
{{ var1 }}
{% if var2 %}
something
{% endif %}
{% for f in var3 %}
{{ f }}
{% endfor %}
"""
        with self.template.open('w') as fp:
            fp.write(self.template_contents)

    def test_init(self):
        io_wrapper = TextIOWrapper(self.template.open('rb'))
        template = utils.Template(io_wrapper)
        self.assertEqual(template._contents, self.template_contents)

    def test_get_vars(self):
        io_wrapper = TextIOWrapper(self.template.open('rb'))
        template = utils.Template(io_wrapper)
        self.assertEqual(template.get_vars(), {'var1', 'var2', 'var3'})

    def tearDown(self):
        rmtree(self.test_dir, ignore_errors=True)


class TestAliasedGroup(TestCase):
    def test_init(self):
        utils.AliasedGroup()

    def test_get_command(self):

        group = utils.AliasedGroup()
        @click.command()
        def remove():
            pass
        @click.command()
        def add():
            pass
        @click.command()
        def delete():
            pass
        group.add_command(remove)
        group.add_command(add)
        group.add_command(delete)
        ctx = click.Context(remove)
        self.assertEqual(group.get_command(ctx, 'remove'), remove)
        self.assertEqual(group.get_command(ctx, 'rm'), remove)
        with self.assertRaises(click.UsageError):
            group.get_command(ctx, 'd')
        self.assertTrue(group.get_command(ctx, 'show') is None)
