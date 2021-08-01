More Information for the Curious
===================================

More on CCSDS-NDM
------------------
The top-level description of the standard is given in the
`Navigation Data — Definitions and Conventions Green Book <https://public.ccsds.org/Pubs/500x0g4.pdf>`_ and
`Navigation Data Messages Overview Green Book <https://public.ccsds.org/Pubs/500x2g2.pdf>`_. Individual data types are
defined in their individual definitions (e.g. `Conjunction Data Message <https://public.ccsds.org/Pubs/508x0b1e2c1.pdf>`_
and `Orbit Data Message <https://public.ccsds.org/Pubs/502x0b2c1e2.pdf>`_). The centre for all the standards are
`CCSDS Mission Operations and Information Management Services Area <https://public.ccsds.org/Publications/MOIMS.aspx>`_.

The Schema files are found in the `SANA Registry <https://sanaregistry.org/r/ndmxml>`_.

Design and Limitations of CCSDS-NDM
-------------------------------------
The object tree is created by `xsdata <https://xsdata.readthedocs.io/en/latest/>`_ library, which also handles parsing
and writing of the XML data. As such, there is no documentation generated for this object tree.

File read is usually fast (on the order of seconds) for small files. That said, KVN parsing for large files can
take some time. A 12 MB OEM file lasts about a minute to parse on a good consumer grade computer.
Due to the fragility of the KVN format and the restrictions the standards put on the order of keys, no
parallelisation has been attempted.

How to Regenerate the NDM Classes from Scratch
------------------------------------------------

While probably not of interest to the casual user, how the XML Schema files are converted to the
object tree classes may be of use to some. Here is the procedure:

1. Download the xsd files from `SANA NDM XML Schema Registry <https://sanaregistry.org/r/ndmxml>`_
2. Run `xsData` just outside the xsd directory to generate the classes

>>> xsdata generate --docstring-style NumPy ndmxml-2.0.0-schemas-unqualified/ --package ccsds_ndm.models.ndmxml2

3. Copy the generated classes into the project structure.
