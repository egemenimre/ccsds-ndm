
# Using XSD and XML files

## Using `generateDS` to convert XSD files to classes that parse and export XML

Use `generateDS` (see [website](https://sourceforge.net/projects/generateds/) and [tutorial](http://www.davekuhlman.org/generateds_tutorial.html)) to convert the xsd file into a bunch of classes that can parse and export an XML file:

`generateDS.py -f -o ccsds_oem_api.py -s ccsds_oem_sub.py --super=ccsds_opm_api ndmxml-1.0-oem-2.0.xsd`

The part with `-s` creates the _sub_ of the _api_, representing a stub that accesses the `api` file structures.

(To install new packages to a conda env see [here](https://stackoverflow.com/questions/57326043/how-to-install-packages-in-conda-that-are-not-available-in-anaconda-conda4-7))

## Using `xmlschema` to parse and validate the XML files via XSD files

See the `xmlschema` docs [here](https://xmlschema.readthedocs.io/en/latest/).

