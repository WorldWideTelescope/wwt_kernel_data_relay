# Copyright 2021 the .NET Foundation
# Licensed under the MIT License

"""
The main module for the WWT kernel data relay Jupyter server extension.

It contains no nontrivial functionality of its own.
"""

from .serverextension import load_jupyter_server_extension  # noqa

# See: https://jupyter.readthedocs.io/en/latest/projects/kernels.html
def _jupyter_server_extension_points():
    return [{"module": "wwt_kernel_data_relay.serverextension"}]

# Backwards compatibility
_jupyter_server_extension_paths = _jupyter_server_extension_points