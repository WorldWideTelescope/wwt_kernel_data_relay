# Copyright 2021 the .NET Foundation
# Licensed under the MIT License

"""
The main module for the WWT kernel data relay Jupyter server extension.

It contains no nontrivial functionality of its own.
"""

from .serverextension import load_jupyter_server_extension  # noqa

# See: https://jupyter-notebook.readthedocs.io/en/stable/examples/Notebook/Distributing%20Jupyter%20Extensions%20as%20Python%20Packages.html
def _jupyter_server_extension_paths():
    return [{"module": "wwt_kernel_data_relay.serverextension"}]
