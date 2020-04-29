import os
from pathlib import Path
from shutil import rmtree
from unittest import TestCase

from clinja import completions

class TestCompletions(TestCase):
    def setUp(self):
        self.test_dir = Path('test_completions')
        self.test_dir.mkdir(exist_ok=True)
        self.files = ['aa', 'bb', 'ab', 'ba']
        for f in self.files:
            (self.test_dir / f).touch()



    def test_get_completions(self):
        for shell in ['bash', 'zsh', 'fish']:
            self.assertTrue(isinstance(completions.get_completions(shell), str))

    def test_variable_names(self):
        completions.variable_names(None, ['command'], '')

    def test_file_names(self):
        cwd = Path.cwd()
        os.chdir(self.test_dir)
        self.assertEqual(completions.file_names(None, None, 'a'), ['ab', 'aa'])
        os.chdir(cwd)

    def test_variable_value(self):
        completions.variable_value(None, ['command', 'full_name'], None)
        completions.variable_value(None, ['command', 'full_name', 'Loic Coyle'], None)

    def tearDown(self):
        rmtree(self.test_dir, ignore_errors=True)

