"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""


class NovaError(Exception):
    """ A low-level error occured in the C library. """

class DuplicateError(Exception):
    """ Either a body or constraint is added to space more than once. """