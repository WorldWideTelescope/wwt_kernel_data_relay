.. _specification:

==============================
WWT KDR Protocol Specification
==============================

This document specifies the interactions between the WWT kernel data relay (KDR)
and various Jupyter kernels that use it to publish data.


URL Structure
=============

The URLs that are ultimately provided by the KDR have the form:

.. code-block::

  {base-url}/wwtkdr/{key}/{entry...}

Here, ``base-url`` is the base URL of the Jupyter notebook server, which is
easily determined on the server side and is not-so-easily determined on the
kernel side. The base URL is not necessarily absolute, however, and there may be
different kinds of proxies or redirectors in place that prevent either the
kernel *or* the server from knowing the true, actual public URL at which their
content is ultimately made available. The only way to reliably construct a fully
absolute URL is in the frontend JavaScript code, by combining a KDR URL with the
current window's ``location``.

The ``key`` is a unique identifier associated with exactly one Jupyter kernel. A
running kernel must “claim” a key before any data it publishes will be
accessible. Later on, a different kernel can override the claim and take over
the association between key and kernel; this functionality is required so that
URLs have the possibility of continuing to work across kernel restarts. A single
kernel may claim multiple keys.

The ``entry...`` identifies resources published by a specific kernel. The
structure and semantics of the ``entry`` portion of the URL are unspecified;
each kernel may use whichever scheme it deems appropriate.


Claiming Keys
=============

A kernel can claim a URL key by publishing a message of type
``wwtkdr_claim_key`` on its `IOPub socket`_. The message content should have the
form:

.. code-block:: json

  {
    'key': $key
  }

Where ``$key`` is the key being claimed by the kernel. This value should not be
empty and it should *not* be URL-escaped.

.. _IOPub socket: https://jupyter-client.readthedocs.io/en/stable/messaging.html


Requesting Resources
====================

When the server receives a request for a KDR URL path, the key will be used to
map the request to a specific kernel. That kernel will be sent a message on its
`shell socket`_ of type ``wwtkdr_resource_request`` with the following content
structure:

.. _shell socket: https://jupyter-client.readthedocs.io/en/stable/messaging.html

.. code-block:: json

  {
    'method': 'GET',
    'entry': $entry,
  }
