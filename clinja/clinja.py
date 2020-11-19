import json
import re
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Union

import click
from myopy import PyFile

from .settings import DYNAMIC_FILE, STATIC_FILE
from .utils import sanitize_variable_name


class ClinjaDynamic:
    def __init__(self, dynamic_file: Path = DYNAMIC_FILE):
        """This class handles clinja's dynamic.py file.

        Args:
            dynamic_file: Path to the dynamic file.
        """
        self.dynamic_file = dynamic_file

    @staticmethod
    def _get_io_path(textio: TextIOWrapper) -> Path:
        """Tries to find the file path of a TextIOWrapper object.

        Args:
            textio: TextIOWrapper instance for which to find the path.

        Returns:
            path to textio's file.
        """
        if not hasattr(textio, "name") or textio.name in ["<stdin>", "<stdout>"]:
            return None
        else:
            return Path(textio.name)

    def run(
        self,
        static_vars: dict = {},
        template: Union[TextIOWrapper, Path] = None,
        destination: Union[TextIOWrapper, Path] = None,
        run_cwd: Path = Path.cwd(),
    ):
        """Runs the python dynamic.py file and returns the variable name and value
        dictionary.

        Args:
            static_vars: The variable names and values from static storage.
            template: The template file.
            destination: The destination file.
            run_cwd: The directory in which the clinja command is run.

        Returns:
            The variable name and values after running the file.
        """
        if isinstance(template, TextIOWrapper):
            template = self._get_io_path(template)
        if isinstance(destination, (click.utils.LazyFile, TextIOWrapper)):
            destination = self._get_io_path(destination)
        if template is not None:
            template = template.resolve()
        if destination is not None:
            destination = destination.resolve()

        dynamic_vars = {}
        conf = PyFile(self.dynamic_file)
        conf.provide(
            TEMPLATE=template,
            DESTINATION=destination,
            RUN_CWD=run_cwd.resolve(),
            STATIC_VARS=static_vars.copy(),
            DYNAMIC_VARS=dynamic_vars,
        )
        conf_module = conf.run()
        return dynamic_vars


class ClinjaStatic:
    def __init__(self, static_file: Path = STATIC_FILE):
        """Handles clinja's static variable names and values.

        Args:
            static_file: Path of the static json file.

        Attributes:
            static_file: Path of the static json file.
        """
        self.static_file = static_file
        self._stored = None

    @property
    def stored(self) -> dict:
        """
        Returns:
            Stored variable names and values.
        """
        if self._stored is None:
            with open(self.static_file, "r") as fp:
                self._stored = json.load(fp)
        return self._stored

    def _write(self):
        """Write `self.stored` to file."""
        with open(self.static_file, "w") as fp:
            json.dump(self.stored, fp, indent=4, sort_keys=True)

    def list(self, pattern=None):
        """Print the stored variable names and values.

        Args:
            pattern: Regex pattern for variable name filtering.

        Returns:
            Iterable on key value pairs of stored variables.
        """
        if pattern is not None:
            pattern = re.compile(pattern)
            return ((k, v) for k, v in self.stored.items() if re.search(pattern, k))
        else:
            return self.stored.items()

    def add(self, variable_name: str, value: Any, force: bool = False):
        """Add a variable name and value to static storage.

        Args:
            variable_name: jinja variable name.
            value: Assigned value.
            force: if True will overwrite any existing value. if False will raise
                ValueError is `variable_name` is already used.

        Raises:
            ValueError: if `force` is False and `variable_name` already exists.
        """
        variable_name = sanitize_variable_name(variable_name)
        if (
            not force
            and variable_name in self.stored.keys()
            and self.stored[variable_name] != value
        ):
            raise ValueError(f'"{variable_name}" already in store.')
        self.stored[variable_name] = value
        self._write()

    def remove(self, variable_name: str):
        """Remove a variable from the static storage.

        Args:
            variable_name: Variable to remove from the store.
        """
        del self.stored[variable_name]
        self._write()
