import click
import clinja
from pathlib import Path
from shutil import rmtree
from unittest import TestCase
from clinja import cli
from click.testing import CliRunner


class DummyContext:
    def __init__(self, obj):
        self.obj = obj


class TestPromptChecks(TestCase):
    def test_value_check(self):
        self.assertEqual(cli.prompt_value_check("something"), "something")
        self.assertEqual(cli.prompt_value_check('["a"]'), ["a"])
        # with self.assertRaises(click.UsageError):
        #     cli.prompt_value_check('[a')

    def test_variable_name_check(self):
        self.assertEqual(cli.prompt_variable_name_check("var1"), "var1")
        with self.assertRaises(click.UsageError):
            cli.prompt_variable_name_check("1")


class TestCli(TestCase):
    def setUp(self):
        self.test_dir = Path("test_cli")
        self.test_dir.mkdir(exist_ok=True)
        self.static_path = self.test_dir / "static.json"
        self.static_content = '{"aa": 1,\n"ab": 2,\n"bb": 3}'
        self.dynamic_path = self.test_dir / "dynamic.py"
        self.template_path = self.test_dir / "template"
        self.template_content = """\
{{ aa }}
{{ bb }}
{{ template }}
{{ missing }}
"""

        with self.static_path.open("w") as fp:
            fp.write(self.static_content)
        with self.dynamic_path.open("w") as fp:
            fp.write(
                """\
DYNAMIC_VARS['template'] = TEMPLATE
DYNAMIC_VARS['destination'] = DESTINATION
DYNAMIC_VARS['run_cwd'] = RUN_CWD
DYNAMIC_VARS['static_vars'] = STATIC_VARS
"""
            )
        with self.template_path.open("w") as fp:
            fp.write(self.template_content)
        self.dynamic_path.touch()
        # self.static_path.touch()

        self.static = clinja.ClinjaStatic(static_file=self.static_path.resolve())
        self.dynamic = clinja.ClinjaDynamic(dynamic_file=self.dynamic_path.resolve())
        self.obj = {"static": self.static, "dynamic": self.dynamic}

    def test_add(self):
        runner = CliRunner()

        res = runner.invoke(cli.add, ["var1", "value1"], obj=self.obj)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("var1" in self.static.stored.keys())
        self.assertEqual(self.static.stored["var1"], "value1")

        res = runner.invoke(cli.add, ["var2", '["a"]'], obj=self.obj)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("var2" in self.static.stored.keys())
        self.assertEqual(self.static.stored["var2"], ["a"])

        res = runner.invoke(cli.add, ["var3", "Loic", "Coyle"], obj=self.obj)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("var3" in self.static.stored.keys())
        self.assertEqual(self.static.stored["var3"], "Loic Coyle")

        res = runner.invoke(cli.add, ["var4", "123"], obj=self.obj)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("var4" in self.static.stored.keys())
        self.assertEqual(self.static.stored["var4"], 123)

        res = runner.invoke(cli.add, ["5", "value5"], obj=self.obj)
        self.assertEqual(res.exit_code, 2)

        res = runner.invoke(
            cli.add, ["var1", "value1_changed"], obj=self.obj, input="n\n"
        )
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("var1" in self.static.stored.keys())
        self.assertEqual(self.static.stored["var1"], "value1")

        res = runner.invoke(
            cli.add, ["var1", "value1_changed"], obj=self.obj, input="y\n"
        )
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("var1" in self.static.stored.keys())
        self.assertEqual(self.static.stored["var1"], "value1_changed")

        res = runner.invoke(cli.add, ["var6"], obj=self.obj, input="value6\n")
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("var6" in self.static.stored.keys())
        self.assertEqual(self.static.stored["var6"], "value6")

        res = runner.invoke(cli.add, obj=self.obj, input="var7\nvalue7\n")
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("var7" in self.static.stored.keys())
        self.assertEqual(self.static.stored["var7"], "value7")

    def test_completion(self):
        runner = CliRunner()
        res = runner.invoke(cli.completion, ["bash"])
        self.assertEqual(res.exit_code, 0)
        res = runner.invoke(cli.completion, ["zsh"])
        self.assertEqual(res.exit_code, 0)
        res = runner.invoke(cli.completion, ["fish"])
        self.assertEqual(res.exit_code, 0)
        res = runner.invoke(cli.completion, ["ksh"])
        self.assertEqual(res.exit_code, 2)

    def test_list(self):
        runner = CliRunner()
        res = runner.invoke(cli.list, obj=self.obj)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.output, "aa: 1\nab: 2\nbb: 3\n")

        res = runner.invoke(cli.list, ["a"], obj=self.obj)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.output, "aa: 1\nab: 2\n")

        res = runner.invoke(cli.list, ["b"], obj=self.obj)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.output, "ab: 2\nbb: 3\n")

        res = runner.invoke(cli.list, ["c"], obj=self.obj)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.output, "")

    def test_remove(self):
        runner = CliRunner()
        res = runner.invoke(cli.remove, ["aa"], obj=self.obj)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("aa" not in self.static.stored.keys())

        res = runner.invoke(cli.remove, ["not_in"], obj=self.obj)
        self.assertEqual(res.exit_code, 1)

        res = runner.invoke(cli.remove, ["bb", "not_in"], obj=self.obj)
        self.assertEqual(res.exit_code, 1)
        self.assertTrue("bb" not in self.static.stored.keys())

    def test_test(self):
        runner = CliRunner()
        res = runner.invoke(cli.test, [], obj=self.obj)
        output = res.output.strip().split("\n")
        static_content = self.static_content.replace("\n", " ").replace('"', "'")
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("destination: None" in output)
        self.assertTrue("template: None" in output)
        self.assertTrue(f"static_vars: {static_content}" in output)
        self.assertTrue(f"run_cwd: {Path.cwd()}" in output)

        res = runner.invoke(
            cli.test,
            [
                "--template",
                "../test",
                "--destination",
                "../../../test",
                "--run_cwd",
                "somewhere/else",
                "--static_vars",
                '{"c": 3}',
            ],
            obj=self.obj,
        )
        output = res.output.strip().split("\n")
        static_content = self.static_content.replace("\n", " ").replace('"', "'")
        self.assertEqual(res.exit_code, 0)
        self.assertTrue(f'destination: {Path("../../../test").resolve()}' in output)
        self.assertTrue(f'template: {Path("../test").resolve()}' in output)
        self.assertTrue("static_vars: {'c': 3}" in output)
        self.assertTrue(f'run_cwd: {Path("somewhere/else").resolve()}' in output)

        res = runner.invoke(
            cli.test,
            [
                "--template",
                "../test",
                "--destination",
                "../../../test",
                "--run_cwd",
                "somewhere/else",
                "--static_vars",
                '{"c": 3',
            ],
            obj=self.obj,
        )
        self.assertEqual(res.exit_code, 1)

    def test_run(self):
        runner = CliRunner()
        res = runner.invoke(
            cli.run, [str(self.template_path), "--prompt", "never"], obj=self.obj
        )
        self.assertEqual(res.exit_code, 1)
        self.assertTrue("missing" in res.output)

        res = runner.invoke(cli.add, ["missing", "value_missing"], obj=self.obj)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue("missing" in self.static.stored.keys())

        res = runner.invoke(
            cli.run, [str(self.template_path), "--prompt", "never"], obj=self.obj
        )
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(
            res.output,
            f"""\
1
3
{self.template_path.resolve()}
value_missing""",
        )

    def tearDown(self):
        rmtree(self.test_dir)
