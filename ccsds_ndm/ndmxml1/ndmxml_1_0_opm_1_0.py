from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional

from ccsds_ndm.ndmxml1.ndmxml_1_0_navwg_common import (
    AngleType,
    DeltamassType,
    DistanceType,
    DurationType,
    GmType,
    InclinationType,
    NdmHeader,
    SpacecraftParametersType,
    StateVectorType,
    VelocityType,
)

__NAMESPACE__ = "urn:ccsds:recommendation:navigation:schema:ndmxml"


@dataclass
class OpmMetadata:
    """
    :ivar comment:
    :ivar object_name:
    :ivar object_id:
    :ivar center_name:
    :ivar ref_frame:
    :ivar time_system:
    """

    class Meta:
        name = "opmMetadata"

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
    time_system: Optional[str] = field(
        default=None,
        metadata={
            "name": "TIME_SYSTEM",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class KeplerianElementsType:
    """
    :ivar comment:
    :ivar semi_major_axis:
    :ivar eccentricity:
    :ivar inclination:
    :ivar ra_of_asc_node:
    :ivar arg_of_pericenter:
    :ivar true_anomaly:
    :ivar mean_anomaly:
    :ivar gm:
    """

    class Meta:
        name = "keplerianElementsType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    semi_major_axis: Optional[DistanceType] = field(
        default=None,
        metadata={
            "name": "SEMI_MAJOR_AXIS",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    eccentricity: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "ECCENTRICITY",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": 0.0,
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
    true_anomaly: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "TRUE_ANOMALY",
            "type": "Element",
            "namespace": "",
        },
    )
    mean_anomaly: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "MEAN_ANOMALY",
            "type": "Element",
            "namespace": "",
        },
    )
    gm: Optional[GmType] = field(
        default=None,
        metadata={
            "name": "GM",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class ManeuverParametersType:
    """
    :ivar comment:
    :ivar man_epoch_ignition:
    :ivar man_duration:
    :ivar man_delta_mass:
    :ivar man_ref_frame:
    :ivar man_dv_1:
    :ivar man_dv_2:
    :ivar man_dv_3:
    """

    class Meta:
        name = "maneuverParametersType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    man_epoch_ignition: Optional[str] = field(
        default=None,
        metadata={
            "name": "MAN_EPOCH_IGNITION",
            "type": "Element",
            "namespace": "",
            "required": True,
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    man_duration: Optional[DurationType] = field(
        default=None,
        metadata={
            "name": "MAN_DURATION",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    man_delta_mass: Optional[DeltamassType] = field(
        default=None,
        metadata={
            "name": "MAN_DELTA_MASS",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    man_ref_frame: Optional[str] = field(
        default=None,
        metadata={
            "name": "MAN_REF_FRAME",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    man_dv_1: Optional[VelocityType] = field(
        default=None,
        metadata={
            "name": "MAN_DV_1",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    man_dv_2: Optional[VelocityType] = field(
        default=None,
        metadata={
            "name": "MAN_DV_2",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    man_dv_3: Optional[VelocityType] = field(
        default=None,
        metadata={
            "name": "MAN_DV_3",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class OpmData:
    """
    :ivar comment:
    :ivar state_vector:
    :ivar keplerian_elements:
    :ivar spacecraft_parameters:
    :ivar maneuver_parameters:
    """

    class Meta:
        name = "opmData"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    state_vector: Optional[StateVectorType] = field(
        default=None,
        metadata={
            "name": "stateVector",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    keplerian_elements: Optional[KeplerianElementsType] = field(
        default=None,
        metadata={
            "name": "keplerianElements",
            "type": "Element",
            "namespace": "",
        },
    )
    spacecraft_parameters: Optional[SpacecraftParametersType] = field(
        default=None,
        metadata={
            "name": "spacecraftParameters",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    maneuver_parameters: List[ManeuverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "maneuverParameters",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class OpmSegment:
    """
    :ivar metadata:
    :ivar data:
    """

    class Meta:
        name = "opmSegment"

    metadata: Optional[OpmMetadata] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    data: Optional[OpmData] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class OpmBody:
    """
    :ivar segment:
    """

    class Meta:
        name = "opmBody"

    segment: Optional[OpmSegment] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class OpmType:
    """
    :ivar header:
    :ivar body:
    :ivar id:
    :ivar version:
    """

    class Meta:
        name = "opmType"

    header: Optional[NdmHeader] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    body: Optional[OpmBody] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    id: str = field(
        init=False,
        default="CCSDS_OPM_VERS",
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    version: str = field(
        init=False,
        default="1.0",
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
