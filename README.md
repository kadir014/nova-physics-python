# Python binding for [Nova Physics Engine](https://github.com/kadir014/nova-physics)
<img src="https://img.shields.io/badge/license-MIT-blue.svg">
<img src="https://img.shields.io/badge/version-0.2.1-yellow">

Python bindings using CFFI for the Nova Physics Engine.

This binding tries to be as Pythonic as possible while trying to keep the original interface the same. So you should be able to use [C library's documentation](https://nova-physics.readthedocs.io/en/latest/).



# Requirements
- [Python](https://www.python.org/downloads/) (3.10+)
- [Setuptools](https://pypi.org/project/setuptools/)
- [Build](https://pypi.org/project/build/)



# Installation
Clone the repo and `cd` into it.
```shell
$ git clone https://github.com/kadir014/nova-physics-python.git
$ cd nova-physics-python
```

Install the package locally. This will also download the latest commit from C library's repository.
```shell
$ pip install .
```

Or if you want to build wheels, follow this.
```shell
$ python -m build
```

Then install the wheel generated under the `dist` directory.
```shell
$ pip install nova-version-yourplatform.whl
```


# License
[MIT](LICENSE) © Kadir Aksoy
