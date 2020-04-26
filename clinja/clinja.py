import json
import click
from io import StringIO
from myopy import PyFile
from typing import Any
from pathlib import Path
from jinja2 import Template
from jinja2 import Environment
from jinja2.meta import find_undeclared_variables

from .settings import CONF_FILE, STORE_FILE


class ClinjaTemplate(Template):
    """Small wrapper to cleanly provide the template in the form of a
    StringIO object.
    """
    def __new__(cls, template: StringIO, *args, **kwargs):
        """
        Parameters:
        -----------
        template:
            Template StringIO object.

        Attributes:
        contents: str
            contents of the template

        """
        contents = template.read()
        template_cls = super().__new__(cls, contents, *args, **kwargs)
        template_cls._contents = contents
        return template_cls

    def get_vars(self) -> set:
        """Gets the variables in the template.

        Returns:
        --------
        set:
            set containing the undeclared variables ofund in the template.
        """
        ast = self.environment.parse(self._contents)
        return find_undeclared_variables(ast)


class ClinjaConfig:
    def __init__(self, config: Path=CONF_FILE):
        """This class handles the clinja config.py file.

        Parameters:
        -----------
        config
            Path to the configuration file.
        """
        self.config = config

    @staticmethod
    def _get_stringio_path(stringio: StringIO) -> Path:
        """Tries to find the file path of a StringIO object.

        Parameters:
        -----------
        stringio
            StringIO instance for which to find the path.

        Returns:
        --------
        Path
            path to stringio's file.
        """
        if stringio is None or stringio.name in ['<stdin>', '<stdout>']:
            return None
        else:
            return Path(stringio.name).absolute()

    def run(self,
            stored: dict={},
            template: StringIO=None,
            destination: StringIO=None):
        """Runs the python config file and returns the variable name and value
        dictionary.

        Parameters:
        -----------
        stored:
            The variable names and values from storage.
        template:
            The template file.
        destination:
            The destination file.

        Returns:
        --------
        dict:
            The variable name and values after running the config file.
        """
        config_vars = stored.copy()
        conf = PyFile(self.config)
        conf.provide('TEMPLATE', self._get_stringio_path(template))
        conf.provide('DESTINATION', self._get_stringio_path(destination))
        conf.provide('RUN_CWD', Path.cwd())
        conf.provide('VARS', config_vars)
        conf_module = conf.run()
        return config_vars


class ClinjaStore:
    def __init__(self, store: Path=STORE_FILE):
        """Handles clinja's variable name/value storage.

        Parameters:
        -----------
        store:
            Path the store json file.

        Attributes:
        -----------
        store:
            Path the store json file.
        """
        self.store = store
        self._stored = None

    @property
    def stored(self) -> dict:
        """
        dict: Stored variable names and values.
        """
        if self._stored is None:
            with open(self.store, 'r') as fp:
                self._stored = json.load(fp)
        return self._stored

    def _write(self):
        """Write `self.stored` to file.
        """
        with open(self.store, 'w') as fp:
            json.dump(self.stored, fp, indent=4, sort_keys=True)

    def list(self):
        """Print the stored variable names and values.
        """
        for k, v in self.stored.items():
            click.echo(f'{click.style(k, bold=True)}: {v}')

    def add(self,
            variable_name: str,
            value: Any,
            force: bool=False):
        """Add a variable name and value to the store file.

        Parameters:
        -----------
        variable_name:
            jinja variable name.
        value:
            Assigned value.
        force:
            if True will overwrite any existing value.
            if False will raise ValueError is `variable_name` is already used.

        Raises:
        -------
        ValueError
            if `force` is False and `variable_name` already exists.
        """
        if not force and variable_name in self.stored.keys():
            raise ValueError(f"\"{variable_name}\" already in store.")
        self.stored[variable_name] = value
        self._write()

    def remove(self, variable_name: str):
        """Remove a variable from the store.

        Parameters:
        -----------
        variable_name:
            Variable to remove from the store.
        """
        del self.stored[variable_name]
        self._write()
