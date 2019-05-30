# cookiecutter installation (with pip)

```
pip install --user cookiecutter
```

# Generating the template

In a terminal, navigate to a location where you want to deploy the `piedpiper.d` folder
```
cd /path/to/picli/tests/functional/my_custom_project
```

To accept the default values located in cookiecutter.json, run:
```
cookiecutter --no-input /path/to/picli/tests/functional
```

To replace some or all default values with user-specified variables, run:
```
cookiecutter /path/to/picli/tests/functional
```
When prompted, press the return key to accept the default (indicated within brackets `[default_value]`) or type in a user-defined value instead.
