# Changelog

- Version 3.0 (2026/08/12)
  - Completely rewritten the KVN read/write engine
  - Introduced support for the older NDM XML Schemas. Now a TDM 1.0 and a TDM 2.0 can be read properly, with their respective NDM XML schemas. ([#20](https://github.com/egemenimre/ccsds-ndm/issues/20))
  - Moved documentation to markdown.
  - Bumped up to the new sphinx versions and cleaned up the build errors.

- Version 2.2 (2021/08/01)
  - Added a proper error message if the user tries to output a Combined NDM to KVN.
    ([#16](https://github.com/egemenimre/ccsds-ndm/issues/16))

- Version 2.1 (2021/05/16)
  - Updated to new `xsdata` (21.5) and `lxml` (4.6.3)
  - Fixed an issue (due to new `xsdata`) where root tags could not be processed correctly

- Version 2.0 (2021/02/22)
  - Major update to support reading KVN data and files
  - Upgraded to NDM XML 2.0.0 XML Schemas
  - Updated `xsdata` to 20.12 (and solved compatibility issues with the new version)
  - Added optional schema file location
    ([#8](https://github.com/egemenimre/ccsds-ndm/issues/8))

- Version 1.3 (2020/12/06)
  - Started stripping single-data Combined Instantiation NDM files
    ([#12](https://github.com/egemenimre/ccsds-ndm/issues/12))

- Version 1.2 (2020/12/02)
  - Added support for Combined Instantiation NDM files
    ([#10](https://github.com/egemenimre/ccsds-ndm/issues/10))

- Version 1.1 (2020/11/25)
  - Modified the internal directory structure to prevent problems with packaging
    ([#9](https://github.com/egemenimre/ccsds-ndm/issues/9))

- Version 1.0 (2020/11/24)
  - First release
