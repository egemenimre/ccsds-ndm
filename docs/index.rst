CCSDS Navigation Data Messages (NDM) Read/Write
=================================================

Description
--------------
The Consultative Committee for Space Data Systems (CCSDS) develops communications and data systems standards
for spaceflight. `CCSDS Navigation Data Messages (NDM) <https://public.ccsds.org/Publications/MOIMS.aspx>`_
is the set of file standards to define common data types such as trajectory, orbit, attitude and conjunction events.
These data types are routinely generated and exchanged within and between spacecraft operators, space agencies,
researchers, amateurs and commercial companies. As such, accurate definition and common interpretation of the data
is crucial (and sometimes mission-critical).

The standard description for each data type is encapsulated in an XML Schema file. This project `ccsds-ndm` aims to
be the reference open-source Python implementation to read and write the NDM XML and KVN files, through an object tree
API, auto-generated by these schema files. It supports the up-to-date NDM XML 2.0.0 standard.

The source code is `on Github <https://github.com/egemenimre/ccsds-ndm>`_.

Current functionality:

.. csv-table::
   :header: "", "Read", "Write"
   :widths: 20, 50, 50

   "XML", "All NDM Types", "All NDM Types"
   "KVN", "All except NDM Combined Instantiation", "All except NDM Combined Instantiation"
   "JSON", "Not specified in CCSDS Standards", "Not specified in CCSDS Standards"


Usage and Examples
-------------------

There are two use cases:

-   The `ccsds-ndm` library reads the NDM file, fills an object tree and offers it to the users. The users will then
    have to fill their own attitude, orbit or trajectory objects used in their libraries.
-   The user fills an object tree from their own attitude, orbit or trajectory object. The `ccsds-ndm` library
    writes the NDM file using this object tree.

For the first use case, reading an OEM file from `xml_read_path` is as simple as:

>>> cdm = NdmIo().from_path(xml_read_path)

Note that file format (XML or KVN) and data type (e.g. CDM or NDM) are inferred automatically.
The output `cdm` is the object tree for a Conjunction Data Message (CDM). The contents can then be reached
going deeper in the object tree as specified in the corresponding NDM Standard. This example shows how to reach the
orbit normal position component of the relative state vector:

>>> print(cdm.body.relative_metadata_data.relative_state_vector.relative_position_n)

The data can sometimes be of type NDM Combined Instantiation. This means that there are multiple NDM data bodies
(e.g. 2 AEMs, 3 OEMs and one OMM) within a single file. The file reader supports these types as well and they are
kept within the `Ndm` object as individual lists for each of the file types. The following example retrieves the
second `Omm` object in the NDM file and then continues to dive deeper into the object tree to retrieve the
eccentricity value.

>>> print(ndm.omm[1].body.segment.data.mean_elements.eccentricity)

If the file is of the type NDM Combined Instantiation but there is only a single data (e.g. OMM) in it,
the ndm tags are stripped and only the single data is presented to the user.

Filling the objects with data properly requires some care. As the standard is understandably strict, the
object tree derived from the XSD files are also rather exacting in how they accept data. Out of these three
different ways of inserting data, the third one is invalid:

>>> # This is valid but missing units information
>>> cdm.body.relative_metadata_data.relative_state_vector.relative_position_r = LengthType(700)
>>>
>>> # This is the proper way to write data into the object
>>> cdm.body.relative_metadata_data.relative_state_vector.relative_position_t = LengthType(Decimal(800), LengthUnits.M)
>>>
>>> # This is invalid
>>> # cdm.body.relative_metadata_data.relative_state_vector.relative_position_r = 600

The output of the above two methods is different on the XML file - the latter is properly
transmitting important unit information:

>>>      <relativeStateVector>
>>>        <RELATIVE_POSITION_R>700</RELATIVE_POSITION_R>
>>>        <RELATIVE_POSITION_T units="m">800</RELATIVE_POSITION_T>

Therefore, care must be taken (and standard documents must be kept as a reference) when mapping
the user objects into the object tree. Valuable information on units, models and methods can be found
there to correctly interpret the data. Also, comments can also be used to provide supplementary information
on how this data is generated.

Finally, once filled with the relevant data, the `cdm` object can be written to `xml_write_path` in XML data format as:

>>> NdmIo().to_file(cdm, NDMFileFormats.XML, xml_write_path)

The `ndm` object trees are not very user friendly and most probably will have to be filled by the users'
own equivalent objects (trajectory, orbit, attitude etc.).

Installing `ccsds-ndm`
-----------------------

The `ccsds-ndm` package is on `PyPI`_ and you can install it simply by running::

    pip install ccsds_ndm

You can also install it via `conda-forge`_::

    conda install -c conda-forge ccsds_ndm

Do not install `ccsds-ndm` using `sudo`.


.. _`PyPI`: https://pypi.org/project/ccsds_ndm/
.. _`conda-forge`: https://anaconda.org/conda-forge/ccsds_ndm

Requirements
------------

-   `xsData` is used to read and write XML files (and also to generate the object tree)
-   `lxml` to support XML object creation

Citation
--------

Please use the DOI for citations. This is the latest version:

|DOI|

Known Issues
------------
-   Some browsers (at least Firefox 82.0 in Dec 2020) strip the namespace information from the XML
    file when the file is viewed. However, when the file is downloaded directly (e.g. through wget),
    the namespace information is kept intact. While neither case causes issues with `ccsds-ndm`, the
    former case may result in the XML viewers to report namespace errors.
    (Hat tip to Juan Luis Cano Rodríguez for spotting this)

Table of Contents
------------------

.. toctree::
    :maxdepth: 1

    changelog.rst
    ndmio.rst
    more_info.rst
    ndmclasses.rst

Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |DOI| image:: https://zenodo.org/badge/312698629.svg
    :target: https://zenodo.org/badge/latestdoi/312698629
    :alt: DOI
