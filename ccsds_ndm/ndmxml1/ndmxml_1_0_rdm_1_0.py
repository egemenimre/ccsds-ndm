from dataclasses import dataclass, field
from typing import List, Optional

from ccsds_ndm.ndmxml1.ndmxml_1_0_navwg_common import (
    AtmosphericReentryParametersType,
    ControlledType,
    DisintegrationType,
    DistanceType,
    GroundImpactParametersType,
    ImpactUncertaintyType,
    ObjectDescriptionType,
    OdParametersType,
    OpmCovarianceMatrixType,
    RdmSpacecraftParametersType,
    ReentryUncertaintyMethodType,
    StateVectorType,
    UserDefinedType,
    YesNoType,
)

__NAMESPACE__ = "urn:ccsds:recommendation:navigation:schema:ndmxml"


@dataclass
class RdmHeader:
    """
    :ivar comment:
    :ivar creation_date:
    :ivar originator:
    :ivar message_id:
    """

    class Meta:
        name = "rdmHeader"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    creation_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "CREATION_DATE",
            "type": "Element",
            "namespace": "",
            "required": True,
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    originator: Optional[str] = field(
        default=None,
        metadata={
            "name": "ORIGINATOR",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    message_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MESSAGE_ID",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class RdmData:
    """
    :ivar comment:
    :ivar atmospheric_reentry_parameters:
    :ivar ground_impact_parameters:
    :ivar state_vector:
    :ivar covariance_matrix:
    :ivar spacecraft_parameters:
    :ivar od_parameters:
    :ivar user_defined_parameters:
    """

    class Meta:
        name = "rdmData"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    atmospheric_reentry_parameters: Optional[AtmosphericReentryParametersType] = field(
        default=None,
        metadata={
            "name": "atmosphericReentryParameters",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    ground_impact_parameters: Optional[GroundImpactParametersType] = field(
        default=None,
        metadata={
            "name": "groundImpactParameters",
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
    spacecraft_parameters: Optional[RdmSpacecraftParametersType] = field(
        default=None,
        metadata={
            "name": "spacecraftParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    od_parameters: Optional[OdParametersType] = field(
        default=None,
        metadata={
            "name": "odParameters",
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
class RdmMetadata:
    """
    :ivar comment:
    :ivar object_name:
    :ivar international_designator:
    :ivar catalog_name:
    :ivar object_designator:
    :ivar object_type:
    :ivar object_owner:
    :ivar object_operator:
    :ivar controlled_reentry:
    :ivar center_name:
    :ivar time_system:
    :ivar epoch_tzero:
    :ivar ref_frame:
    :ivar ref_frame_epoch:
    :ivar ephemeris_name:
    :ivar gravity_model:
    :ivar atmospheric_model:
    :ivar solar_flux_prediction:
    :ivar n_body_perturbations:
    :ivar solar_rad_pressure:
    :ivar earth_tides:
    :ivar intrack_thrust:
    :ivar drag_parameters_source:
    :ivar drag_parameters_altitude:
    :ivar reentry_uncertainty_method:
    :ivar reentry_disintegration:
    :ivar impact_uncertainty_method:
    :ivar previous_message_id:
    :ivar previous_message_epoch:
    :ivar next_message_epoch:
    """

    class Meta:
        name = "rdmMetadata"

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
    international_designator: Optional[str] = field(
        default=None,
        metadata={
            "name": "INTERNATIONAL_DESIGNATOR",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    catalog_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "CATALOG_NAME",
            "type": "Element",
            "namespace": "",
        },
    )
    object_designator: Optional[str] = field(
        default=None,
        metadata={
            "name": "OBJECT_DESIGNATOR",
            "type": "Element",
            "namespace": "",
        },
    )
    object_type: Optional[ObjectDescriptionType] = field(
        default=None,
        metadata={
            "name": "OBJECT_TYPE",
            "type": "Element",
            "namespace": "",
        },
    )
    object_owner: Optional[str] = field(
        default=None,
        metadata={
            "name": "OBJECT_OWNER",
            "type": "Element",
            "namespace": "",
        },
    )
    object_operator: Optional[str] = field(
        default=None,
        metadata={
            "name": "OBJECT_OPERATOR",
            "type": "Element",
            "namespace": "",
        },
    )
    controlled_reentry: Optional[ControlledType] = field(
        default=None,
        metadata={
            "name": "CONTROLLED_REENTRY",
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
    time_system: Optional[str] = field(
        default=None,
        metadata={
            "name": "TIME_SYSTEM",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    epoch_tzero: Optional[str] = field(
        default=None,
        metadata={
            "name": "EPOCH_TZERO",
            "type": "Element",
            "namespace": "",
            "required": True,
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    ref_frame: Optional[str] = field(
        default=None,
        metadata={
            "name": "REF_FRAME",
            "type": "Element",
            "namespace": "",
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
    ephemeris_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "EPHEMERIS_NAME",
            "type": "Element",
            "namespace": "",
        },
    )
    gravity_model: Optional[str] = field(
        default=None,
        metadata={
            "name": "GRAVITY_MODEL",
            "type": "Element",
            "namespace": "",
        },
    )
    atmospheric_model: Optional[str] = field(
        default=None,
        metadata={
            "name": "ATMOSPHERIC_MODEL",
            "type": "Element",
            "namespace": "",
        },
    )
    solar_flux_prediction: Optional[str] = field(
        default=None,
        metadata={
            "name": "SOLAR_FLUX_PREDICTION",
            "type": "Element",
            "namespace": "",
        },
    )
    n_body_perturbations: Optional[str] = field(
        default=None,
        metadata={
            "name": "N_BODY_PERTURBATIONS",
            "type": "Element",
            "namespace": "",
        },
    )
    solar_rad_pressure: Optional[str] = field(
        default=None,
        metadata={
            "name": "SOLAR_RAD_PRESSURE",
            "type": "Element",
            "namespace": "",
        },
    )
    earth_tides: Optional[str] = field(
        default=None,
        metadata={
            "name": "EARTH_TIDES",
            "type": "Element",
            "namespace": "",
        },
    )
    intrack_thrust: Optional[YesNoType] = field(
        default=None,
        metadata={
            "name": "INTRACK_THRUST",
            "type": "Element",
            "namespace": "",
        },
    )
    drag_parameters_source: Optional[str] = field(
        default=None,
        metadata={
            "name": "DRAG_PARAMETERS_SOURCE",
            "type": "Element",
            "namespace": "",
        },
    )
    drag_parameters_altitude: Optional[DistanceType] = field(
        default=None,
        metadata={
            "name": "DRAG_PARAMETERS_ALTITUDE",
            "type": "Element",
            "namespace": "",
        },
    )
    reentry_uncertainty_method: Optional[ReentryUncertaintyMethodType] = field(
        default=None,
        metadata={
            "name": "REENTRY_UNCERTAINTY_METHOD",
            "type": "Element",
            "namespace": "",
        },
    )
    reentry_disintegration: Optional[DisintegrationType] = field(
        default=None,
        metadata={
            "name": "REENTRY_DISINTEGRATION",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_uncertainty_method: Optional[ImpactUncertaintyType] = field(
        default=None,
        metadata={
            "name": "IMPACT_UNCERTAINTY_METHOD",
            "type": "Element",
            "namespace": "",
        },
    )
    previous_message_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PREVIOUS_MESSAGE_ID",
            "type": "Element",
            "namespace": "",
        },
    )
    previous_message_epoch: Optional[str] = field(
        default=None,
        metadata={
            "name": "PREVIOUS_MESSAGE_EPOCH",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    next_message_epoch: Optional[str] = field(
        default=None,
        metadata={
            "name": "NEXT_MESSAGE_EPOCH",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )


@dataclass
class RdmSegment:
    """
    :ivar metadata:
    :ivar data:
    """

    class Meta:
        name = "rdmSegment"

    metadata: Optional[RdmMetadata] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    data: Optional[RdmData] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class RdmBody:
    """
    :ivar segment:
    """

    class Meta:
        name = "rdmBody"

    segment: Optional[RdmSegment] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class RdmType:
    """
    :ivar header:
    :ivar body:
    :ivar id:
    :ivar version:
    """

    class Meta:
        name = "rdmType"

    header: Optional[RdmHeader] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    body: Optional[RdmBody] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    id: str = field(
        init=False,
        default="CCSDS_RDM_VERS",
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
