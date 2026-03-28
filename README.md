# Pyrecracker
Pyrcracker is a python module that can be used to create, run, and manage the lifecycle of micro virtual machines using Firecracker.  Pyrecracker gives a simple to use API for VM management that can be used from within python based applications.

## Supported Operating Systems
The following are the operating systems that pyrecracker has been tested on:
- Ubuntu 24.04 LTS (with nested virtualization enabled)

## Installing
If using pip, pyrecracker can be installed with:

```
pip install pyrecracker
```

If using poetry, pyrecracker can be installed with:

```
poetry add pyrecracker
```

## Building
This project uses poetry for building and packaging.  Pyrecracker can be built with the following command:

```
poetry build
```

This will generate the project's tar.gz and .whl files in the `./dist` directory.

## Testing
Unit tests can be run with the following:

```
poetry run pytest
```

Examples on using pyrecracker can be found in the `./examples` directory.