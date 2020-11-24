More Information for the Curious
===================================

More on CCSDS-NDM
------------------
The top-level description of the standard is given in the
`Navigation Data — Definitions and Conventions Green Book <https://public.ccsds.org/Pubs/500x0g4.pdf>`_ and
`Navigation Data Messages Overview Green Book <https://public.ccsds.org/Pubs/500x2g2.pdf>`_. Individual data types are
defined in their individual definitions (e.g. `Conjunction Data Message <https://public.ccsds.org/Pubs/508x0b1e2c1.pdf>`_
and `Orbit Data Message <https://public.ccsds.org/Pubs/502x0b2c1.pdf>`_). The centre for all the standards are
`CCSDS Mission Operations and Information Management Services Area <https://public.ccsds.org/Publications/MOIMS.aspx>`_.

The Schema files are found in the `SANA Registry <https://sanaregistry.org/r/ndmxml>`_.

Design and Limitations of CCSDS-NDM
-------------------------------------
The object tree is created by `xsdata <https://xsdata.readthedocs.io/en/latest/>`_ library, which also handles parsing
and writing of the XML data. As such, there is no documentation generated for this object tree.

Currently the published standards are at version 1.0, but version 2.0 will be out soon. They will be integrated into
the code once they are made official.

How to Regenerate the NDM Classes from Scratch
------------------------------------------------

While probably not of interest to the casual user, how the XML Schema files are converted to the
object tree classes may be of use to some. Here is the procedure:

1. Download the xsd files from `SANA NDM XML Schema Registry <https://sanaregistry.org/r/ndmxml>`_
2. Run `xsData` just outside the xsd directory to generate the classes

>>> xsdata generate ndmxsd --package src.ndmxml1

3. Copy the generated classes into the project structure.

The newer versions of the NDM XML files will go to the `ndmxml2` directory, so that backwards compatibility
is maintained.