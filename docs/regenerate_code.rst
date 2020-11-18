How to Regenerate the NDM Classes from Scratch
==============================================

1. Download the xsd files from `SANA NDM XML Schema Registry <https://sanaregistry.org/r/ndmxml>`_
2. Run `xsData` just outside the xsd directory to generate the classes

>>> xsdata generate ndmxsd --package src.examples.xsdata_example.ndmxml

3. Run `pyment` to convert ReST docstrings to numpy docstrings (???)