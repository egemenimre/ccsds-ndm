from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from ccsds_ndm.models.ndmxml2.ndmxml_2_0_0_common_2_0 import (
    AngleType,
    DistanceType,
    GmType,
    InclinationType,
    NdmHeader,
    OpmCovarianceMatrixType,
    SpacecraftParametersType,
    UserDefinedType,
)

__NAMESPACE__ = "urn:ccsds:schema:ndmxml"


class BStarUnits(Enum):
    VALUE_1_ER = "1/ER"


class DRevUnits(Enum):
    REV_DAY_2 = "rev/day**2"
    REV_DAY_2_1 = "REV/DAY**2"


class DdRevUnits(Enum):
    REV_DAY_3 = "rev/day**3"
    REV_DAY_3_1 = "REV/DAY**3"


@dataclass
class OmmMetadata:
    class Meta:
        name = "ommMetadata"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    object_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "OBJECT_NAME",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    object_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OBJECT_ID",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    center_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "CENTER_NAME",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    ref_frame: Optional[str] = field(
        default=None,
        metadata={
            "name": "REF_FRAME",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    ref_frame_epoch: Optional[str] = field(
        default=None,
        metadata={
            "name": "REF_FRAME_EPOCH",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    time_system: Optional[str] = field(
        default=None,
        metadata={
            "name": "TIME_SYSTEM",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    mean_element_theory: Optional[str] = field(
        default=None,
        metadata={
            "name": "MEAN_ELEMENT_THEORY",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


class RevUnits(Enum):
    REV_DAY = "rev/day"
    REV_DAY_1 = "REV/DAY"


@dataclass
class BStarType:
    class Meta:
        name = "bStarType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[BStarUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DRevType:
    class Meta:
        name = "dRevType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[DRevUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DdRevType:
    class Meta:
        name = "ddRevType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[DdRevUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class RevType:
    class Meta:
        name = "revType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[RevUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class MeanElementsType:
    class Meta:
        name = "meanElementsType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    epoch: Optional[str] = field(
        default=None,
        metadata={
            "name": "EPOCH",
            "type": "Element",
            "namespace": "",
            "required": True,
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    semi_major_axis: Optional[DistanceType] = field(
        default=None,
        metadata={
            "name": "SEMI_MAJOR_AXIS",
            "type": "Element",
            "namespace": "",
        },
    )
    mean_motion: Optional[RevType] = field(
        default=None,
        metadata={
            "name": "MEAN_MOTION",
            "type": "Element",
            "namespace": "",
        },
    )
    eccentricity: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "ECCENTRICITY",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": Decimal("0.0"),
        },
    )
    inclination: Optional[InclinationType] = field(
        default=None,
        metadata={
            "name": "INCLINATION",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    ra_of_asc_node: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "RA_OF_ASC_NODE",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    arg_of_pericenter: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "ARG_OF_PERICENTER",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    mean_anomaly: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "MEAN_ANOMALY",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    gm: Optional[GmType] = field(
        default=None,
        metadata={
            "name": "GM",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class TleParametersType:
    class Meta:
        name = "tleParametersType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    ephemeris_type: Optional[int] = field(
        default=None,
        metadata={
            "name": "EPHEMERIS_TYPE",
            "type": "Element",
            "namespace": "",
        },
    )
    classification_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "CLASSIFICATION_TYPE",
            "type": "Element",
            "namespace": "",
        },
    )
    norad_cat_id: Optional[int] = field(
        default=None,
        metadata={
            "name": "NORAD_CAT_ID",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    element_set_no: Optional[int] = field(
        default=None,
        metadata={
            "name": "ELEMENT_SET_NO",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": 0,
            "max_inclusive": 9999,
        },
    )
    rev_at_epoch: Optional[int] = field(
        default=None,
        metadata={
            "name": "REV_AT_EPOCH",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    bstar: Optional[BStarType] = field(
        default=None,
        metadata={
            "name": "BSTAR",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    mean_motion_dot: Optional[DRevType] = field(
        default=None,
        metadata={
            "name": "MEAN_MOTION_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    mean_motion_ddot: Optional[DdRevType] = field(
        default=None,
        metadata={
            "name": "MEAN_MOTION_DDOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class OmmData:
    class Meta:
        name = "ommData"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    mean_elements: Optional[MeanElementsType] = field(
        default=None,
        metadata={
            "name": "meanElements",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    spacecraft_parameters: Optional[SpacecraftParametersType] = field(
        default=None,
        metadata={
            "name": "spacecraftParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    tle_parameters: Optional[TleParametersType] = field(
        default=None,
        metadata={
            "name": "tleParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    covariance_matrix: Optional[OpmCovarianceMatrixType] = field(
        default=None,
        metadata={
            "name": "covarianceMatrix",
            "type": "Element",
            "namespace": "",
        },
    )
    user_defined_parameters: Optional[UserDefinedType] = field(
        default=None,
        metadata={
            "name": "userDefinedParameters",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class OmmSegment:
    class Meta:
        name = "ommSegment"

    metadata: Optional[OmmMetadata] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    data: Optional[OmmData] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class OmmBody:
    class Meta:
        name = "ommBody"

    segment: Optional[OmmSegment] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class OmmType:
    class Meta:
        name = "ommType"

    header: Optional[NdmHeader] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    body: Optional[OmmBody] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    id: str = field(
        init=False,
        default="CCSDS_OMM_VERS",
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    version: str = field(
        init=False,
        default="2.0",
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
