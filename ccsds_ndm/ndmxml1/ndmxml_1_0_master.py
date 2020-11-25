from dataclasses import dataclass

from ccsds_ndm.ndmxml1.ndmxml_1_0_aem_1_0 import AemType
from ccsds_ndm.ndmxml1.ndmxml_1_0_apm_1_0 import ApmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_cdm_1_0 import CdmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_ndm_1_0 import NdmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_oem_2_0 import OemType
from ccsds_ndm.ndmxml1.ndmxml_1_0_omm_2_0 import OmmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_opm_1_0 import OpmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_rdm_1_0 import RdmType
from ccsds_ndm.ndmxml1.ndmxml_1_0_tdm_2_0 import TdmType


@dataclass
class Aem(AemType):
    class Meta:
        name = "aem"


@dataclass
class Apm(ApmType):
    class Meta:
        name = "apm"


@dataclass
class Cdm(CdmType):
    class Meta:
        name = "cdm"


@dataclass
class Ndm(NdmType):
    class Meta:
        name = "ndm"


@dataclass
class Oem(OemType):
    class Meta:
        name = "oem"


@dataclass
class Omm(OmmType):
    class Meta:
        name = "omm"


@dataclass
class Opm(OpmType):
    class Meta:
        name = "opm"


@dataclass
class Rdm(RdmType):
    class Meta:
        name = "rdm"


@dataclass
class Tdm(TdmType):
    class Meta:
        name = "tdm"
