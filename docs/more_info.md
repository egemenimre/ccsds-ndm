# More Information for the Curious

## More on CCSDS-NDM

The top-level description of the standard is given in the [Navigation Data — Definitions and Conventions Green Book](https://public.ccsds.org/Pubs/500x0g4.pdf) and [Navigation Data Messages Overview Green Book](https://public.ccsds.org/Pubs/500x2g2.pdf). Individual data types are defined in their individual definitions (e.g. [Conjunction Data Message](https://public.ccsds.org/Pubs/508x0b1e2c1.pdf) and [Orbit Data Message](https://public.ccsds.org/Pubs/502x0b2c1e2.pdf)). The centre for all the standards are [CCSDS Mission Operations and Information Management Services Area](https://public.ccsds.org/Publications/MOIMS.aspx).

The Schema files are found in the [SANA Registry](https://sanaregistry.org/r/ndmxml).

## Design and Limitations of CCSDS-NDM

The object tree is created by [xsdata](https://xsdata.readthedocs.io/en/latest/) library, which also handles parsing and writing of the XML data. As such, there is no detailed documentation generated for this object tree.

File read is usually fast (on the order of milliseconds) for small files. That said, KVN parsing for large files can take some time. Due to the fragility of the KVN format and the restrictions the standards put on the order of keys, no parallelisation has been attempted.

## How to Regenerate the NDM Classes from Scratch

While probably not of interest to the casual user, how the XML Schema files are converted to the object tree classes may be of use to some. Here is the procedure:

1. Download the xsd files from [SANA NDM XML Schema Registry](https://sanaregistry.org/r/ndmxml)
2. Run `xsData` just outside the xsd directory to generate the classes

    ```bash
    xsdata generate --include-header --docstring-style NumPy ndmxml-4.0.C-schemas-unqualified/ --package ccsds_ndm.models.ndmxml4
    ```

3. Copy the generated classes into the `models` directory in the project structure.
4. Create the new model in the `kvn_registry`, with the new version, e.g., `self.version: int = 5`. This step is not trivial, as it requires understanding the differences with respect to the previous version. However, an AI agent should be able to handle it easily.
