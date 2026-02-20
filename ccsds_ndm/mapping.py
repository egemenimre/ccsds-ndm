# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
CCSDS Navigation Data Messages Mappings

"""

from enum import Enum, auto

from ccsds_ndm.models import ndmxml1, ndmxml2, ndmxml4


class NDMFileFormats(Enum):
    """
    NDM file formats.
    """

    XML = auto()
    KVN = auto()
    JSON = auto()


class _NdmDataType(Enum):
    """
    Enumeration of NDM (Navigation Data Message) data types and their associated metadata.

    This enum maps NDM data types (such as OEM, AEM, APM, etc.) to their corresponding
    XML schema classes, versions, and schema versions. It provides a centralized registry
    for parsing and rendering NDM XML data according to CCSDS NDM XML schemas.

    Parameters
    ----------
    ndm_id : str
        NDM data identifier in lowercase (e.g., 'aem', 'oem', 'ndm')
    clazz : type
        Class corresponding to the NDM data type, used for XML parsing and rendering
        Version string of the NDM data type (e.g., '1.0', '2.0', '3.0', '4.0')
    req_combi_version : int
        Required NDM XML schema version required for this NDM data type
    is_combi : bool
        Flag indicating whether this NDM type can contain multiple data types
        (True for combined NDM containers, False for individual data types)

    Notes
    -----
    - Each enum member represents a specific NDM data type and version combination
    - The class attribute references generated xsdata classes from ndmxml1, ndmxml2, and ndmxml4
    """

    ACMv2 = (ndmxml4.Acm.Meta.name, ndmxml4.Acm, "2.0", 4, False)

    AEMv1 = (ndmxml2.Aem.Meta.name, ndmxml2.Aem, "1.0", 2, False)
    AEMv2 = (ndmxml4.Aem.Meta.name, ndmxml4.Aem, "2.0", 4, False)

    APMv1 = (ndmxml2.Apm.Meta.name, ndmxml2.Apm, "1.0", 2, False)
    APMv2 = (ndmxml4.Apm.Meta.name, ndmxml4.Apm, "2.0", 4, False)

    CDMv1 = (ndmxml4.Cdm.Meta.name, ndmxml4.Cdm, "1.0", 4, False)

    OCMv3 = (ndmxml4.Ocm.Meta.name, ndmxml4.Ocm, "3.0", 4, False)

    OEMv2 = (ndmxml2.Oem.Meta.name, ndmxml2.Oem, "2.0", 2, False)
    OEMv3 = (ndmxml4.Oem.Meta.name, ndmxml4.Oem, "3.0", 4, False)

    OMMv2 = (ndmxml2.Omm.Meta.name, ndmxml2.Omm, "2.0", 2, False)
    OMMv3 = (ndmxml4.Omm.Meta.name, ndmxml4.Omm, "3.0", 4, False)

    OPMv2 = (ndmxml2.Opm.Meta.name, ndmxml2.Opm, "2.0", 2, False)
    OPMv3 = (ndmxml4.Opm.Meta.name, ndmxml4.Opm, "3.0", 4, False)

    RDMv1 = (ndmxml4.Rdm.Meta.name, ndmxml4.Rdm, "1.0", 4, False)

    TDMv1 = (ndmxml1.Tdm.Meta.name, ndmxml1.Tdm, "1.0", 2, False)
    TDMv2 = (ndmxml4.Tdm.Meta.name, ndmxml4.Tdm, "2.0", 4, False)

    # The following can contain multiple NDM Data Types
    # (e.g. OMM, APM etc.) and are identified as "NDM" in the XML tag.
    NDMv2 = (ndmxml2.Ndm.Meta.name, ndmxml2.Ndm, "2.0", 2, True)
    NDMv4 = (ndmxml4.Ndm.Meta.name, ndmxml4.Ndm, "4.0", 4, True)

    def __init__(
        self, ndm_id: str, clazz, version: str, req_combi_version: int, is_combi
    ):
        self.clazz = clazz
        self.ndm_id = ndm_id.strip()
        self.version = version.strip()
        self.req_combi_version = req_combi_version
        self.is_combi = is_combi

    @staticmethod
    def find_element(ndm_id, version) -> "_NdmDataType":
        """
        Finds the NDM Data Type corresponding to the requested id.

        Parameters
        ----------
        ndm_id : str
            NDM data id (e.g. `aem` or `ndm`)
        version : str
            Version of the NDM data type
        Returns
        -------
        ndm_data_type
            correct `_NdmDataType` enum corresponding to the id
        """
        for ndm_data in _NdmDataType:
            if ndm_data.ndm_id == ndm_id and ndm_data.version == version:
                return ndm_data

        raise ValueError(
            f"No NDM data type found for id '{ndm_id}' and version '{version}'"
        )

    @staticmethod
    def find_combi_version(ndm_type: "_NdmDataType") -> "_NdmDataType":
        """
        Finds the appropriate combined NDM version for a given NDM data type.

        Parameters
        ----------
        ndm_type : _NdmDataType
            The NDM data type for which to find the combined version

        Returns
        -------
        _NdmDataType
            The appropriate combined NDM version that supports the given NDM data type
        """
        for ndm_data in _NdmDataType:
            if (
                ndm_data.is_combi
                and ndm_data.req_combi_version >= ndm_type.req_combi_version
            ):
                return ndm_data

        raise ValueError(
            f"No combined NDM version found that supports the required version for {ndm_type}"
        )
