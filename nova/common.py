"""

    This file is a part of the Nova Physics Engine
    Python Binding and distributed under the MIT license.

    Repository: https://github.com/kadir014/nova-physics-python
    Issues:     https://github.com/kadir014/nova-physics-python/issues

"""

import _nova


lib = _nova.lib
ffi = _nova.ffi


def get_error_buffer() -> str:
    error_buf = ffi.string(lib.nv_get_error())
    return error_buf.decode("utf-8")


def get_version_buffer() -> str:
    error_buf = ffi.string(lib.nv_get_version())
    return error_buf.decode("utf-8")