---
created: 2024/10/15
---
# Using the built in venv for python

## Create an environment

### opena  terminal

```bash
cd /path/to/your/project
```

on windows you can right click on the folder, at press "Open in Terminal"

### create a new environment

```bash
python -m venv .venv
```

This will create a `.venv` folder with the environment.
`.venv` is the name of the newly created virtual environment. You can choose any name, but it's common to name it`venv` or `env`.

### actiavte the environment

On Linus/macOS

```bash
source .venv/bin/activate
```

On Windows

```bash
.venv\Scripts\activate
```

## install project.toml dependencies
```bash
pip install .
```

## deactivate your evironment

```bash
deactivate
```
