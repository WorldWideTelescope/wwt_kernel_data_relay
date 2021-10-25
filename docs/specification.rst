.. _specification:

==============================
WWT KDR Protocol Specification
==============================

This document specifies the interactions between the WWT kernel data relay (KDR)
and various Jupyter kernels that use it to publish data. The reference kernel
implmentation is found in `pywwt`_.

.. _pywwt: https://github.com/WorldWideTelescope/pywwt/


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
current window's ``location``, or in a server request handler where the request
origin is specified.

The ``key`` is a unique identifier associated with exactly one Jupyter kernel. A
running kernel must “claim” a key before any data it publishes will be
accessible. Later on, a different kernel can override the claim and take over
the association between key and kernel; this functionality is required so that
URLs have the possibility of continuing to work across kernel restarts. A single
kernel may claim multiple keys. Keys starting with an underscore character
(``_``) are reserved and may not be claimed.

The ``entry...`` identifies resources published by a specific kernel. The
structure and semantics of the ``entry`` portion of the URL are unspecified;
each kernel may use whichever scheme it deems appropriate.


Claiming Keys
=============

A kernel can claim a URL key by publishing a message of type
``wwtkdr_claim_key`` on its `IOPub socket`_. The message content should have the
form:

.. code-block::

  {
    'key': $key:str
  }

Where ``$key`` is the key being claimed by the kernel. This value should not be
empty and it should *not* be URL-escaped. If the claimed key is illegal (e.g. it
starts with an underscore) or the claim message is otherwise invalid, it is
ignored by the server.

.. _IOPub socket: https://jupyter-client.readthedocs.io/en/stable/messaging.html


Requesting Resources
====================

When the server receives an HTTP request for a KDR URL path, the key will be
used to map the request to a specific kernel. If the key is unregistered, or if
it is associated with a dead kernel, the requestor will receive a 404 error.

On a valid HTTP GET request, the associated kernel will be sent a message on its
`shell socket`_ of type ``wwtkdr_resource_request`` with the following content
structure:

.. _shell socket: https://jupyter-client.readthedocs.io/en/stable/messaging.html

.. code-block::

  {
    'method': 'GET',
    'authenticated': $authenticated:bool,
    'url': $url:str,
    'key': $key:str,
    'entry': $entry:str
  }

The ``$key`` string provides the key of the request URL. Because a kernel can
claim more than one key, it is needed for disambiguation. The key value has been
decoded: if the literal URL text is ``my%2Fkey``, the value if ``$key`` will be
``my/key``.

The ``$url`` string gives the absolute URL of the HTTP request. Due to the way
that the Tornado framework works, there are some normalizations that are applied
before the KDR can do anything about it: ``foo/../bar`` becomes ``bar``, and
``./foo`` becomes ``foo``. But other constructs, such as ``foo//bar``, are not
normalized.

The ``$entry`` string identifies the resource being requested. The relay is not
responsible for, or capable of, checking its validity. For the time being, the
value is merely extracted from the URL and relayed to the kernel, including the
normalizations described above. Clients should use this value instead of trying
to parse anything out of ``$url``.

The ``$authenticated`` boolean indicates whether the request is coming from an
authenticated client, as determined by the Tornado framework. It is up to the
kernel to determine if unauthenticated users should be allowed to access the
resources that it publishes.

The kernel should reply on its shell socket with one or more messages of type
``wwtkdr_resource_reply``. While every reply message must contain some baseline
JSON content, the *first* reply message must contain additional fields
(analogous to HTTP header data). Every reply message, except for the last one,
must also be associated with one or more byte buffers, which contain the
resource binary content to be returned to the client that has connected to the
notebook server. The final reply message is allowed to arrive without any
associated buffers.

The JSON content of the *every* reply message should contain the following fields:

.. code-block::

  {
    'status': $status:str,
    'seq': $seq:int,
    'more': $more:bool
  }

Furthermore, the JSON content of the *first* reply message should contain the
following additional fields:

.. code-block::

  {
    'http_status': $httpStatus:int,
    'http_headers': $httpHeaders:list<[str, str]>,
  }

The ``$status`` field is a Jupyter messaging status indicator. It should be
``"ok"`` if the request was processed successfully (even if the resulting HTTP
status is an error status). If an error was encountered, the value should be
``"error"``, and the structure of the reply should be as described in `the
jupyter_client documentation`_. The value of the ``evalue`` JSON field, if
present, will be relayed to the requestor as part of an HTTP 500 error.

.. _the jupyter_client documentation: https://jupyter-client.readthedocs.io/en/stable/messaging.html#request-reply

The ``$seq`` field gives a sequence number for each reply message, starting at
zero and increasing by one with each reply. This is needed because some
implementations of the Jupyter messaging protocol don't guarantee in-order
message delivery.

The ``$more`` field indicates whether more reply messages will be sent. If your
implementation doesn't "know" when the last reply will be sent until all data
have been transferred, send a final message with no associated byte buffers.

On the first reply, the ``$httpStatus`` field should give an HTTP status code
that will be relayed to the requesting client. The ``$httpHeaders`` field should
be a list of sub-lists, each sub-list consisting of two strings: an HTTP header
name and a header value. These will be included in the HTTP response issued by
the relay, and should include fields such as ``Content-Type``.


Support Interfaces
==================

The KDR provides one additional support API. New APIs, or extensions to existing
APIs, may be added in the future.

Probe API
---------

A request to the following URL may be used by a frontend to probe whether the
KDR server extension is available:

.. code-block::

  {base-url}/wwtkdr/_probe

If the extension is installed, the following JSON content will be returned:

.. code-block::

  {
    'status': 'ok'
  }

This API is marked as requiring authentication, so it must be accessed from a
session that is logged into the current Jupyter session.
