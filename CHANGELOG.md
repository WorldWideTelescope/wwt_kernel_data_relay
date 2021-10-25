# wwt_kernel_data_relay 0.2.0 (2021-10-25)

- Require and use message sequencing numbers in kernel replies (#2, @pkgw).
  These weren't necessary in my initial testing, but in the BinderHub I have
  issues with out-of-order and duplicated messages that make it look like we'll
  have to use these.


# wwt_kernel_data_relay 0.1.1 (2021-10-23)

- Add the drop-in configuration files needed to automatically activate the
  server extension upon package installation (#1, @pkgw).


# wwt_kernel_data_relay 0.1.0 (2021-10-14)

Initial release of the WWT Kernel Data Relay package.
