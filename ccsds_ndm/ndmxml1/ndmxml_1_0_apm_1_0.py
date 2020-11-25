from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from ccsds_ndm.ndmxml1.ndmxml_1_0_navwg_common import (
    AngleRateType,
    AngleType,
    DurationType,
    MomentType,
    NdmHeader,
    QuaternionRateType,
    QuaternionType,
    RotationAngleType,
    RotationRateType,
    RotDirectionType,
    RotseqType,
    TimeSystemType,
)

__NAMESPACE__ = "urn:ccsds:recommendation:navigation:schema:ndmxml"


class ApmRateFrameType(Enum):
    """
    :cvar EULER_FRAME_A:
    :cvar EULER_FRAME_B:
    """

    EULER_FRAME_A = "EULER_FRAME_A"
    EULER_FRAME_B = "EULER_FRAME_B"


class TorqueUnits(Enum):
    """
    :cvar N_M:
    """

    N_M = "N*m"


@dataclass
class ApmMetadata:
    """
    :ivar comment:
    :ivar object_name:
    :ivar object_id:
    :ivar center_name:
    :ivar time_system:
    """

    class Meta:
        name = "apmMetadata"

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
        },
    )
    time_system: Optional[TimeSystemType] = field(
        default=None,
        metadata={
            "name": "TIME_SYSTEM",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class AttSpacecraftParametersType:
    """
    :ivar comment:
    :ivar inertia_ref_frame:
    :ivar i11:
    :ivar i22:
    :ivar i33:
    :ivar i12:
    :ivar i13:
    :ivar i23:
    """

    class Meta:
        name = "attSpacecraftParametersType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    inertia_ref_frame: Optional[str] = field(
        default=None,
        metadata={
            "name": "INERTIA_REF_FRAME",
            "type": "Element",
            "namespace": "",
        },
    )
    i11: Optional[MomentType] = field(
        default=None,
        metadata={
            "name": "I11",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    i22: Optional[MomentType] = field(
        default=None,
        metadata={
            "name": "I22",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    i33: Optional[MomentType] = field(
        default=None,
        metadata={
            "name": "I33",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    i12: Optional[MomentType] = field(
        default=None,
        metadata={
            "name": "I12",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    i13: Optional[MomentType] = field(
        default=None,
        metadata={
            "name": "I13",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    i23: Optional[MomentType] = field(
        default=None,
        metadata={
            "name": "I23",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class EulerElementsSpinType:
    """
    :ivar comment:
    :ivar spin_frame_a:
    :ivar spin_frame_b:
    :ivar spin_dir:
    :ivar spin_alpha:
    :ivar spin_delta:
    :ivar spin_angle:
    :ivar spin_angle_vel:
    :ivar nutation:
    :ivar nutation_per:
    :ivar nutation_phase:
    """

    class Meta:
        name = "eulerElementsSpinType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    spin_frame_a: Optional[str] = field(
        default=None,
        metadata={
            "name": "SPIN_FRAME_A",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    spin_frame_b: Optional[str] = field(
        default=None,
        metadata={
            "name": "SPIN_FRAME_B",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    spin_dir: Optional[RotDirectionType] = field(
        default=None,
        metadata={
            "name": "SPIN_DIR",
            "type": "Element",
            "namespace": "",
        },
    )
    spin_alpha: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "SPIN_ALPHA",
            "type": "Element",
            "namespace": "",
        },
    )
    spin_delta: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "SPIN_DELTA",
            "type": "Element",
            "namespace": "",
        },
    )
    spin_angle: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "SPIN_ANGLE",
            "type": "Element",
            "namespace": "",
        },
    )
    spin_angle_vel: Optional[AngleRateType] = field(
        default=None,
        metadata={
            "name": "SPIN_ANGLE_VEL",
            "type": "Element",
            "namespace": "",
        },
    )
    nutation: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "NUTATION",
            "type": "Element",
            "namespace": "",
        },
    )
    nutation_per: Optional[DurationType] = field(
        default=None,
        metadata={
            "name": "NUTATION_PER",
            "type": "Element",
            "namespace": "",
        },
    )
    nutation_phase: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "NUTATION_PHASE",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class EulerElementsThreeType:
    """
    :ivar comment:
    :ivar euler_frame_a:
    :ivar euler_frame_b:
    :ivar euler_dir:
    :ivar euler_rot_seq:
    :ivar rate_frame:
    :ivar rotation_angles:
    :ivar rotation_rates:
    """

    class Meta:
        name = "eulerElementsThreeType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    euler_frame_a: Optional[str] = field(
        default=None,
        metadata={
            "name": "EULER_FRAME_A",
            "type": "Element",
            "namespace": "",
        },
    )
    euler_frame_b: Optional[str] = field(
        default=None,
        metadata={
            "name": "EULER_FRAME_B",
            "type": "Element",
            "namespace": "",
        },
    )
    euler_dir: Optional[RotDirectionType] = field(
        default=None,
        metadata={
            "name": "EULER_DIR",
            "type": "Element",
            "namespace": "",
        },
    )
    euler_rot_seq: Optional[RotseqType] = field(
        default=None,
        metadata={
            "name": "EULER_ROT_SEQ",
            "type": "Element",
            "namespace": "",
        },
    )
    rate_frame: Optional[ApmRateFrameType] = field(
        default=None,
        metadata={
            "name": "RATE_FRAME",
            "type": "Element",
            "namespace": "",
        },
    )
    rotation_angles: Optional[RotationAngleType] = field(
        default=None,
        metadata={
            "name": "rotationAngles",
            "type": "Element",
            "namespace": "",
        },
    )
    rotation_rates: Optional[RotationRateType] = field(
        default=None,
        metadata={
            "name": "rotationRates",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class QuaternionStateType:
    """
    :ivar comment:
    :ivar epoch:
    :ivar q_frame_a:
    :ivar q_frame_b:
    :ivar q_dir:
    :ivar quaternion:
    :ivar quaternion_rate:
    """

    class Meta:
        name = "quaternionStateType"

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
    q_frame_a: Optional[str] = field(
        default=None,
        metadata={
            "name": "Q_FRAME_A",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    q_frame_b: Optional[str] = field(
        default=None,
        metadata={
            "name": "Q_FRAME_B",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    q_dir: Optional[RotDirectionType] = field(
        default=None,
        metadata={
            "name": "Q_DIR",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    quaternion: Optional[QuaternionType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    quaternion_rate: Optional[QuaternionRateType] = field(
        default=None,
        metadata={
            "name": "quaternionRate",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class TorqueType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "torqueType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[TorqueUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AttManeuverParametersType:
    """
    :ivar comment:
    :ivar man_epoch_start:
    :ivar man_duration:
    :ivar man_ref_frame:
    :ivar man_tor_1:
    :ivar man_tor_2:
    :ivar man_tor_3:
    """

    class Meta:
        name = "attManeuverParametersType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    man_epoch_start: Optional[str] = field(
        default=None,
        metadata={
            "name": "MAN_EPOCH_START",
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
    man_ref_frame: Optional[str] = field(
        default=None,
        metadata={
            "name": "MAN_REF_FRAME",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    man_tor_1: Optional[TorqueType] = field(
        default=None,
        metadata={
            "name": "MAN_TOR_1",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    man_tor_2: Optional[TorqueType] = field(
        default=None,
        metadata={
            "name": "MAN_TOR_2",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    man_tor_3: Optional[TorqueType] = field(
        default=None,
        metadata={
            "name": "MAN_TOR_3",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class ApmData:
    """
    :ivar comment:
    :ivar quaternion_state:
    :ivar euler_elements_three:
    :ivar euler_elements_spin:
    :ivar spacecraft_parameters:
    :ivar maneuver_parameters:
    """

    class Meta:
        name = "apmData"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    quaternion_state: Optional[QuaternionStateType] = field(
        default=None,
        metadata={
            "name": "quaternionState",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    euler_elements_three: Optional[EulerElementsThreeType] = field(
        default=None,
        metadata={
            "name": "eulerElementsThree",
            "type": "Element",
            "namespace": "",
        },
    )
    euler_elements_spin: Optional[EulerElementsSpinType] = field(
        default=None,
        metadata={
            "name": "eulerElementsSpin",
            "type": "Element",
            "namespace": "",
        },
    )
    spacecraft_parameters: Optional[AttSpacecraftParametersType] = field(
        default=None,
        metadata={
            "name": "spacecraftParameters",
            "type": "Element",
            "namespace": "",
        },
    )
    maneuver_parameters: List[AttManeuverParametersType] = field(
        default_factory=list,
        metadata={
            "name": "maneuverParameters",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class ApmSegment:
    """
    :ivar metadata:
    :ivar data:
    """

    class Meta:
        name = "apmSegment"

    metadata: Optional[ApmMetadata] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    data: Optional[ApmData] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class ApmBody:
    """
    :ivar segment:
    """

    class Meta:
        name = "apmBody"

    segment: Optional[ApmSegment] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class ApmType:
    """
    :ivar header:
    :ivar body:
    :ivar id:
    :ivar version:
    """

    class Meta:
        name = "apmType"

    header: Optional[NdmHeader] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    body: Optional[ApmBody] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    id: str = field(
        init=False,
        default="CCSDS_APM_VERS",
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
