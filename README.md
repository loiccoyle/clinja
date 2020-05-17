<p align="center">
  <img src="https://i.imgur.com/9RtyTib.gif">
</p>
<h5 align="center">A jinja CLI.</h5>
<p align="center">
  <a href="https://github.com/loiccoyle/clinja/workflows/tests/"><img src="https://github.com/loiccoyle/clinja/workflows/tests/badge.svg"></a>
  <a href="./LICENSE.md"><img src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <a href="https://pypi.org/project/clinja/"><img src="https://img.shields.io/pypi/v/clinja"></a>
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS%7C%20windows-informational">
</p>

clinja is a versatile command line interface for [`jinja`](https://github.com/pallets/jinja).

# Instalation

clinja should run just fine on Windows, macOS and Linux, to install open up a terminal and run:
```
pip install clinja
```

As always, it's a good idea to use a virtual env, or maybe consider using [`pipx`](https://github.com/pipxproject/pipx).

##### To generate \<tab\> completion for your shell run:
```bash
# Bash:
clinja completions bash > /etc/bash_completion.d/clinja.bash-completion

# Bash (Homebrew)
clinja completions bash > $(brew --prefix)/etc/bash_completion.d/clinja.bash-completion

# Fish:
clinja completions fish > ~/.config/fish/completions/clinja.fish

# Fish (Homebrew)
clinja completions fish > $(brew --prefix)/share/fish/vendor_completions.d/clinja.fish

# Zsh
clinja completions zsh > /somewhere/in/your/fpath/_clinja

# Zsh (Homebrew)
clinja completions zsh > $(brew --prefix)/share/zsh/site-functions/_clinja
```

# Dependencies
clinja relies on the following dependencies:
* python3
* [`jinja`](https://github.com/pallets/jinja): the templating engine.
* [`click`](https://github.com/pallets/click): for the command line interface and completion.
* [`myopy`](https://github.com/loiccoyle/myopy): to run the **dynamic** source python file.

# How it works
When you run clinja on a template containing some `jinja` variables to fill in, clinja will fetch values for these variables from 2 sources.

#### The static source
The **static** source is simply a json file which contains unchanging, static, key value pairs, a la `cookiecutter`'s `cookiecutter.json` file. This is where you would want to add your name, email, username etc. You have full control over these values and can easily manage the stored values using clinja.

#### The dynamic source
This is where things get a bit more interesting, clinja can also get values from a so called **dynamic** source, check the [wiki](https://github.com/loiccoyle/clinja/wiki) for some examples. This source is a python file, with a few variables provided to it at run time. The provided variables are:
```python
TEMPLATE  # Pathlib Path to the template, is None when using stdin.
DESTINATION  # Pathlib Path to the destination, is None when using stdout.
RUN_CWD  # Pathlib Path, Directory were the clinja command was run.
STATIC_VARS  # Dictionary of static variables.
DYNAMIC_VARS  # Dictionary of dynamic variables, initially empty, populated by the dynamic file.
```
With this file you can do some nifty things, such as [automatically determining the name of the git repo in which the completed template will live in](https://github.com/loiccoyle/clinja/wiki/git-repository-name). Any values computed in this file should be added to the ```DYNAMIC_VARS``` dict.

#### Missing variables
When clinja runs into a variable it can't get from either the **static** or the **dynamic** source, it will prompt you for a value, and offer to store it in the **static** file for later use.

# Usage
```
$ clinja --help
Usage: clinja [OPTIONS] COMMAND [ARGS]...

  A versatile jinja command line interface.

  Clinja uses two sources to find values for jinja variables. A
  static source, which is just a json file, and a dynamic
  source, which is a python source file. Clinja populates the static
  source with user entered values. Whereas the dynamic variables are
  computed at run time by the python file.

  In short:

      Clinja stores all static variables in:
      /home/lcoyle/.config/clinja/static.json

      Clinja's dynamic variables are computed by the python file:
      /home/lcoyle/.config/clinja/dynamic.py

Options:
  --help  Show this message and exit.

Commands:
  add         Add a variable to static storage.
  completion  Generate autocompletion for your shell.
  list        List stored static variable(s).
  remove      Remove stored static variable(s).
  run         Run jinja on a template.
  test        Test run your dynamic.py file.
```
#### Static variables:
To manage the **static** variables, use the subcommands: `clinja add`, `clinja remove` and `clinja list`. They should be self explanatory.

#### Dynamic variables:
```
$ clinja test --help
Usage: clinja test [OPTIONS]

  Test run your dynamic.py file.

  Run your dynamic.py file using mock values.

  template, destination, run_cwd and static_vars are provided to the
  dynamic.py file in their respective variable names.

Options:
  --template PATH     mock template path.
  --destination PATH  mock template path.
  --run_cwd PATH      mock current working directory path.
  --static_vars TEXT  mock json format static variables.
  --help              Show this message and exit.

```
The `clinja test` subcommand is provided to help setup and test your **dynamic** source. It allows you to provide any values to the [`dynamic` source's input variables](#The-dynamic-source), run the `dynamic.py` file and will print out the results.

#### Run jinja
```
$ clinja run --help
Usage: clinja run [OPTIONS] [TEMPLATE] [DESTINATION]

  Run jinja on a template.

  TEMPLATE (optional, default: stdin): template file on which to run jinja,
  if using stdin, --prompt is set to "never".

  DESTINATION (optional, default: stdout): output destination.

Options:
  --prompt [always|missing|never]
                                  When to prompt for variable values.
  -d, --dry-run                   Dry run, won't write any files or change/add
                                  any static values.

  --help                          Show this message and exit.
```
###### --prompt
* Using `--prompt always`, will use the values fetched from both sources as defaults and prompt you for each variable's value, giving you a chance to overwrite.
* Using `--prompt missing`, will only prompt you for the variables it can't find a value for.
* Using `--prompt never`, will never prompt and will fail if clinja encounters a variable for which it has no value.

###### -d
The `-d` flag will do a dry run, no files will be written and your **static** source will not change.

<sub>This is part 2 of my ongoing personal mission to improve template handling from the command line, see part 1: [tmpl](https://github.com/loiccoyle/tmpl.sh).</sub>
