import json
import click
import sys
from io import TextIOWrapper
from clinja.clinja import ClinjaStatic
from clinja.clinja import ClinjaDynamic
from unittest import TestCase
from pathlib import Path
from shutil import rmtree

class TestClinjaStatic(TestCase):
    def setUp(self):
        self.test_dir = Path('test_clinja')
        self.static_file = self.test_dir / 'static.json'
        self.static_dict = {'email': 'test@test.com',
                            'name': 'John Doe'}
        self.test_dir.mkdir(exist_ok=True)
        with self.static_file.open('w') as fp:
            fp.write(json.dumps(self.static_dict))

        self.static = ClinjaStatic(self.static_file)

    def test_list(self):
        self.assertTrue(self.static.list(), self.static_dict.items())
        self.assertTrue(self.static.list(pattern='name'),
                       ((k, v) for k, v in {'name': self.static_dict['name']}))

    def test_add(self):
        with self.assertRaises(ValueError):
            self.static.add('name', 'Jane Doe')
        with self.assertRaises(ValueError):
            self.static.add('123', 'Jane Doe')
        with self.assertRaises(ValueError):
            self.static.add('no spaces allowed', 'Jane Doe')

        self.static.add('partner', 'Jane Doe')
        self.assertEqual(self.static.stored['partner'], 'Jane Doe')

    def test_remove(self):
        with self.assertRaises(KeyError):
            self.static.remove('not_in_store')
        self.static.remove('name')
        self.assertTrue('name' not in self.static.stored.keys())

    def tearDown(self):
        rmtree(self.test_dir, ignore_errors=True)


class testClinjaDynamic(TestCase):
    def setUp(self):
        self.test_dir = Path('test_clinja')
        self.test_template = self.test_dir / 'test_template'
        self.dynamic_file = self.test_dir / 'dynamic.py'
        self.dynamic_content ="""
DYNAMIC_VARS['from_static'] = STATIC_VARS['name'] + ' Apple'
DYNAMIC_VARS['template_path'] = TEMPLATE
DYNAMIC_VARS['destination_path'] = DESTINATION
DYNAMIC_VARS['run_cwd'] = RUN_CWD
"""
        self.test_dir.mkdir(exist_ok=True)
        self.test_template.touch()
        with self.dynamic_file.open('w') as fp:
            fp.write(self.dynamic_content)

        self.dynamic = ClinjaDynamic(self.dynamic_file)

    def test_run(self):
        with self.assertRaises(KeyError):
            self.dynamic.run()
        out = self.dynamic.run(static_vars={'name': 'John'})
        self.assertEqual(out['from_static'], 'John Apple')
        self.assertEqual(out['template_path'], None)
        self.assertEqual(out['destination_path'], None)
        self.assertEqual(out['run_cwd'], Path.cwd())

        out = self.dynamic.run(template=Path('test_template'),
                               destination=Path('test_destination'),
                               run_cwd=Path('test_run_cwd'),
                               static_vars={'name': 'John'})
        self.assertEqual(out['from_static'], 'John Apple')
        self.assertEqual(out['template_path'], Path('test_template').resolve())
        self.assertEqual(out['destination_path'], Path('test_destination').resolve())
        self.assertEqual(out['run_cwd'], Path('test_run_cwd').resolve())

        out = self.dynamic.run(template=TextIOWrapper(self.test_template.open('r')),
                               destination=TextIOWrapper(self.test_template.open('r')),
                               run_cwd=Path('test_run_cwd'),
                               static_vars={'name': 'John'})
        self.assertEqual(out['from_static'], 'John Apple')
        self.assertEqual(out['template_path'], self.test_template.resolve())
        self.assertEqual(out['destination_path'], self.test_template.resolve())
        self.assertEqual(out['run_cwd'], Path('test_run_cwd').resolve())

    def tearDown(self):
        rmtree(self.test_dir, ignore_errors=True)
