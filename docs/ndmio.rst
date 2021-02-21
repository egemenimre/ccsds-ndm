File Read and Write through `ndm_io`
=====================================

Top Level Interface `ndm_io`
-----------------------------

The `ndm_io` module is the single unified interface to handle the read and write functionalities for the data
in XML or KVN format. It reads the data, converts it to a string, determines the format and calls the lower level
XML and KML modules to handle the input string. These modules then automatically determine the data type
(e.g. CDM or OMM) and process the file accordingly.

While the nominal use is
reading the data file through the :meth:`.NdmIo.from_path`, it is also possible to read from
a string (with the contents of the file) through :meth:`.NdmIo.from_string` and also from bytes
through :meth:`.NdmIo.from_bytes`.

Similarly, writing an output XML or KVN file through :meth:`.NdmIo.to_file` is probably the most common operation.
This requires the object tree, the data format :class:`.NDMFileFormats` and the output file
path as well as optional arguments, if available. For example, for the case of XML, the URL for the schema
can be provided through the keywords `schema_location` or `no_namespace_schema_location`.


::

    NdmIo().to_file(ndm, NDMFileFormats.XML, xml_write_path,
        no_namespace_schema_location="http://cwe.ccsds.org/moims/docs/MOIMS-NAV/Schemas/ndmxml-1.0-master.xsd")


It is still possible to generate a string output of the file contents through :meth:`.NdmIo.to_string`.
`NdmIo` acts as a thin interface and the actual output of the data is handled by the lower level
:meth:`.NdmKvnIo.from_path` or :meth:`.NdmXmlIo.from_path` classes.

Lower Level Modules `ndm_xml_io` and `ndm_kvn_io`
--------------------------------------------------

The actual parsing and output of the data is carried out in the XML and KVN specific modules. If the user is
sure of the input data type, these modules can be used directly. The interface is the same as the `NdmIo` class;
a KVN or XML file would be parsed via :meth:`.NdmKvnIo.from_path` or :meth:`.NdmXmlIo.from_path`, skipping the file
type specification. Once the data is read, the data type is automatically determined and the file is read into the
object tree.

The XML data read and write is simple and is handled by the underlying `xsdata`engine. The `ndm_xml_io` module simply
provides a simple I/O interface and makes sure the `ndm` data type is handled correctly, which is not always
read properly.

On the other hand, for the parsing of the KVN
data, a template object tree is created using the nested class structure of the object tree and is then populated by
the contents of the data. As such, the KVN parser is agnostic, in the sense that it does not *know* how a CDM KVN file
looks like, but, inspecting the object tree derived from the XSD file, it *finds out* how to read it. Therefore there
are no individual parsers for each file type, but a single "parsing engine". There are a lot of exceptions to the
standard KVN input (such as data lines in AEM and OEM files), which requires these special cases to be handled
separately.

KVN output is possible through :meth:`.NdmKvnIo.to_file` or :meth:`.NdmKvnIo.to_string` methods, to a file or to
a string, respectively. Similar to the parsing engine, there is an output engine that prepares the output string. For
many output types this simply outputs the data in the NDM object in standard KVN format. However, many exceptions exist
(such as OEM, AEM and TDM files) and they have to be handled separately.

Reference/API
-------------
.. automodule:: ccsds_ndm.ndm_io
    :undoc-members:
    :members:

.. automodule:: ccsds_ndm.ndm_xml_io
    :undoc-members:
    :members:

.. automodule:: ccsds_ndm.ndm_kvn_io
    :undoc-members:
    :members: