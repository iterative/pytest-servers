pytest servers
--------------

|PyPI| |Status| |Python Version| |License|

|Tests| |Codecov| |pre-commit| |Black|

.. |PyPI| image:: https://img.shields.io/pypi/v/pytest-servers.svg
   :target: https://pypi.org/project/pytest-servers/
   :alt: PyPI
.. |Status| image:: https://img.shields.io/pypi/status/pytest-servers.svg
   :target: https://pypi.org/project/pytest-servers/
   :alt: Status
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/pytest-servers
   :target: https://pypi.org/project/pytest-servers
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/pytest-servers
   :target: https://opensource.org/licenses/Apache-2.0
   :alt: License
.. |Tests| image:: https://github.com/iterative/pytest-servers/workflows/Tests/badge.svg
   :target: https://github.com/iterative/pytest-servers/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/iterative/pytest-servers/branch/main/graph/badge.svg
   :target: https://app.codecov.io/gh/iterative/pytest-servers
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black


Features
--------

Create temporary directories on the following filesystems:

- Local fs
- In-memory fs
- S3, both using mock S3 remotes (https://github.com/spulec/moto) and real S3 remotes
- Azure, both using mock Azure remotes (https://github.com/Azure/Azurite) via docker and using real Azure Storage remotes
- Google Cloud Storage, both using mock GCS remote (https://github.com/fsouza/fake-gcs-server) via docker and using real Google Storage Remotes

Installation
------------

You can install *pytest servers* via pip_ from PyPI_:

.. code:: console

   $ pip install pytest-servers

To use temporary S3 paths:

.. code:: console

   $ pip install pytest-servers[s3]

To use temporary Azure paths

.. code:: console

   $ pip install pytest-servers[azure]

To use temporary Google Cloud Storage paths

.. code:: console

    $ pip install pytest-servers[gcs]

To install all extras:

.. code:: console

   $ pip install pytest-servers[all]

Usage
------------

The main fixture provided by `pytest-servers` provides is `tmp_upath_factory`, which can be used
to generate temporary paths on different (mocked) filesystems:

.. code:: python

   def test_something_on_s3(tmp_upath_factory):
       path = tmp_upath_factory.mktemp("s3")
       foo = path / "foo"
       foo.write_text("foo")
       ...

`mktemp` supports the following filesystem types:

- ``local`` (local filesystem)
- ``memory`` (in-memory filesystem)
- ``s3`` (Amazon S3)
- ``gcs`` (Google Cloud Storage)
- ``azure`` (Azure Storage)

Some convenience fixtures that wrap `tmp_upath_factory.mktemp` and return a paths on these filesystems are also available:

- ``tmp_local_path``
- ``tmp_memory_path``
- ``tmp_s3_path``
- ``tmp_gcs_path``
- ``tmp_azure_path``

The `tmp_upath` fixture can be used for parametrizing paths with pytest's indirect parametrization:

.. code:: python

   @pytest.mark.parametrize("tmp_upath", ["local", "s3", "gcs", "gs"], indirect=True)
   def test_something(tmp_upath):
       pass

In order to use real remotes instead of mocked ones, use `tmp_upath_factory` with the following methods

- ``tmp_upath_factory.s3(region_name, client_kwargs)`` where client_kwargs are passed to the underlying S3FileSystem/boto client
- ``tmp_upath_factory.gcs(endpoint_url)``
- ``tmp_upath_factory.azure(connection_string)``


Versioning support can be used by using the `versioning` fixture. This is currently supported for s3 and gcs remotes

.. code:: python

   # using mktemp
   def test_something_on_s3_versioned(tmp_upath_factory):
       path = tmp_upath_factory.mktemp("s3", version_aware=True)
       assert path.fs.version_aware # bucket has versioning enabled

   # or, using remote-specific fixtures
   def test_something_on_s3_versioned(tmp_s3_path, versioning):
       assert tmp_s3_path.fs.version_aware # bucket has versioning enabled


Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.

License
--------------
Distributed under the terms of the `Apache 2.0 license`_,
*pytest servers* is free and open source software.

Issues
-------------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


.. _Apache 2.0 license: https://opensource.org/licenses/Apache-2.0
.. _PyPI: https://pypi.org/
.. _file an issue: https://github.com/iterative/pytest-servers/issues
.. _pip: https://pip.pypa.io/
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
