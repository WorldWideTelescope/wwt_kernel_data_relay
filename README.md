[![Build Status](https://dev.azure.com/aasworldwidetelescope/WWT/_apis/build/status/WorldWideTelescope.wwt_kernel_data_relay?branchName=master)](https://dev.azure.com/aasworldwidetelescope/WWT/_build/latest?definitionId=27&branchName=master)

# WWT Kernel Data Relay

<!--pypi-begin-->
[wwt_kernel_data_relay] is a [Jupyter server extension][ext] that enables
[Jupyter kernels][kernels] to publish some of their data files to the Web; that
is, to request that the Jupyter HTTP server make them accessible at a
predictable URL. This functionality is used by [pywwt], the [AAS] [WorldWide
Telescope] Python library, to expose kernel-side data assets for visualization
inside the WWT [research app][rapp].

[wwt_kernel_data_relay]: https://github.com/WorldWideTelescope/wwt_kernel_data_relay/
[ext]: https://jupyter-notebook.readthedocs.io/en/stable/extending/handlers.html
[kernels]: https://jupyter.readthedocs.io/en/latest/projects/kernels.html
[pywwt]: https://pywwt.readthedocs.io/
[AAS]: https://aas.org/
[WorldWide Telescope]: http://www.worldwidetelescope.org/
[rapp]: https://docs.worldwidetelescope.org/research-app/latest/
<!--pypi-end-->


## Installation

Install [wwt_kernel_data_relay] with [pip]:

```
pip install wwt_kernel_data_relay
```

[pip]: https://pip.pypa.io/


## Contributions

Contributions to [wwt_kernel_data_relay] are welcome! See
[the WorldWide Telescope contributors’ guide][contrib] for applicable information. We
use a standard workflow with issues and pull requests. All participants in
[wwt_kernel_data_relay] and the WWT communities must abide by the
[WWT Code of Conduct].

[contrib]: https://worldwidetelescope.github.io/contributing/
[WWT Code of Conduct]: https://worldwidetelescope.github.io/code-of-conduct/


## Release History

Releases of [wwt_kernel_data_relay] are logged in the file
[CHANGELOG.md](https://github.com/WorldWideTelescope/wwt_kernel_data_relay/blob/release/CHANGELOG.md)
on the `release` branch of this repository, as well as release listings
maintained by
[GitHub](https://github.com/WorldWideTelescope/wwt_kernel_data_relay/releases) and
[PyPI](https://pypi.org/project/wwt_kernel_data_relay/#history).


## Dependencies

[wwt_kernel_data_relay] is a [Jupyter server extension][ext] so it is only
useful if the Jupyter [notebook] package is installed.

[notebook]: https://jupyter-notebook.readthedocs.io/


## Legalities

[wwt_kernel_data_relay] is copyright the .NET Foundation. It is licensed under the
[MIT License](./LICENSE).


## Acknowledgments

[wwt_kernel_data_relay] is part of the AAS WorldWide Telescope system, a [.NET
Foundation] project managed by the non-profit [American Astronomical Society]
(AAS). Work on WWT has been supported by the AAS, the US [National Science
Foundation], and other partners. See [the WWT user website][acks] for details.

[.NET Foundation]: https://dotnetfoundation.org/
[American Astronomical Society]: https://aas.org/
[National Science Foundation]: https://www.nsf.gov/
[acks]: https://worldwidetelescope.org/about/acknowledgments/
