# Python binding for [Nova Physics Engine](https://github.com/kadir014/nova-physics)
Python bindings using CFFI for Nova Physics Engine.



# Requirements
- [Python](https://www.python.org/downloads/) (3.10+)
- [Setuptools](https://pypi.org/project/setuptools/)
- [Build](https://pypi.org/project/build/)



# Installation
Clone the repo and `cd` into it.
```sh
$ git clone https://github.com/kadir014/nova-physics-python.git
```

Build the wheel, this will also download the latest commit from C repository.
```sh
$ python -m build
```

Install the wheel generated under the `dist` directory.
```sh
$ pip install nova-version-yourplatform.whl
```


# License
[MIT](LICENSE) © Kadir Aksoy
