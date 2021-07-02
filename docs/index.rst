=============================
WWT Jupyter Kernel Data Relay
=============================

`wwt_kernel_data_relay`_ is a `Jupyter server extension`_ that enables `Jupyter
kernels`_ to publish some of their data files to the Web; that is, to request
that the Jupyter HTTP server make them accessible at a predictable URL. This
functionality is used by `pywwt`_ to expose kernel-side data assets for
visualization inside the `WWT research app`_.

.. _wwt_kernel_data_relay: https://github.com/WorldWideTelescope/wwt_kernel_data_relay/
.. _Jupyter server extension: https://jupyter-notebook.readthedocs.io/en/stable/extending/handlers.html
.. _Jupyter kernels: https://jupyter.readthedocs.io/en/latest/projects/kernels.html
.. _pywwt: https://pywwt.readthedocs.io/
.. _WWT research app: https://docs.worldwidetelescope.org/research-app/latest/


Detailed Table of Contents
==========================

.. toctree::
   :maxdepth: 2

   installation
   specification
   api


Getting help
============

If you run into any issues when using `wwt_kernel_data_relay`_, please open an
issue `on its GitHub repository
<https://github.com/WorldWideTelescope/wwt_kernel_data_relay/issues>`_.


Acknowledgments
===============

`wwt_kernel_data_relay`_ is part of the `AAS`_ `WorldWide Telescope`_ system, a
`.NET Foundation`_ project managed by the non-profit `American Astronomical
Society`_ (AAS). Work on WWT has been supported by the AAS, the US `National
Science Foundation`_, and other partners. See `the WWT user website`_ for
details.

.. _.NET Foundation: https://dotnetfoundation.org/
.. _AAS: https://aas.org/
.. _WorldWide Telescope: https://worldwidetelescope.org/home/
.. _American Astronomical Society: https://aas.org/
.. _National Science Foundation: https://www.nsf.gov/
.. _the WWT user website: https://worldwidetelescope.org/about/acknowledgments/