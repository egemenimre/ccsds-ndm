from dataclasses import dataclass, field
from typing import List

from ccsds_ndm.ndmxml1.ndmxml_1_0_aem_1_0 import AemType
from ccsds_ndm.ndmxml1.ndmxml_1_0_apm_1_0 import ApmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_cdm_1_0 import CdmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_oem_2_0 import OemType
from ccsds_ndm.ndmxml1.ndmxml_1_0_omm_2_0 import OmmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_opm_1_0 import OpmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_rdm_1_0 import RdmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_tdm_2_0 import TdmType

__NAMESPACE__ = "urn:ccsds:recommendation:navigation:schema:ndmxml"


@dataclass
class NdmType:
    """
    :ivar comment:
    :ivar aem:
    :ivar apm:
    :ivar cdm:
    :ivar oem:
    :ivar omm:
    :ivar opm:
    :ivar rdm:
    :ivar tdm:
    """

    class Meta:
        name = "ndmType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    aem: List[AemType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "sequential": True,
        },
    )
    apm: List[ApmType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "sequential": True,
        },
    )
    cdm: List[CdmType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "sequential": True,
        },
    )
    oem: List[OemType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "sequential": True,
        },
    )
    omm: List[OmmType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "sequential": True,
        },
    )
    opm: List[OpmType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "sequential": True,
        },
    )
    rdm: List[RdmType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "sequential": True,
        },
    )
    tdm: List[TdmType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "sequential": True,
        },
    )
