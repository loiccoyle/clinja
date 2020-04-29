import click
from unittest import TestCase
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
            pass
        self.assertEqual(func_test.__doc__, '2')

    def test_bold(self):
        self.assertEqual(utils.bold('bla'), '\x1b[1mbla\x1b[0m')
