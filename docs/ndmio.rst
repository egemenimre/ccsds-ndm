`ndm_io` Package
==============================

The `ndm_io` package handles the read and write of the XML data.

While the nominal use is
reading the required XML file through the :meth:`.NdmIo.from_path`, it is also possible to read from
a string (with the contents of the XML file) through :meth:`.NdmIo.from_string` and also from bytes
through :meth:`.NdmIo.from_bytes`.

Similarly, writing an XML file through :meth:`.NdmIo.to_file` is probably the most common operation.
However, it is still possible to generate a string output of the XML file through
:meth:`.NdmIo.to_string`.

Reference/API
-------------
.. automodule:: ccsds_ndm.ndm_io
    :undoc-members:
    :members: