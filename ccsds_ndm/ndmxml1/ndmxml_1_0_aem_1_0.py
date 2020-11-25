from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from ccsds_ndm.ndmxml1.ndmxml_1_0_navwg_common import (
    AngleRateType,
    AngleType,
    DurationType,
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


class AemRateFrameType(Enum):
    """
    :cvar REF_FRAME_A:
    :cvar REF_FRAME_A_1:
    :cvar REF_FRAME_B:
    :cvar REF_FRAME_B_1:
    """

    REF_FRAME_A = "ref_frame_a"
    REF_FRAME_A_1 = "REF_FRAME_A"
    REF_FRAME_B = "ref_frame_b"
    REF_FRAME_B_1 = "REF_FRAME_B"


class AttitudeTypeType(Enum):
    """
    :cvar QUATERNION:
    :cvar QUATERNION_1:
    :cvar QUATERNION_DERIVATIVE:
    :cvar QUATERNION_DERIVATIVE_1:
    :cvar QUATERNION_RATE:
    :cvar QUATERNION_RATE_1:
    :cvar EULER_ANGLE:
    :cvar EULER_ANGLE_1:
    :cvar EULER_ANGLE_RATE:
    :cvar EULER_ANGLE_RATE_1:
    :cvar SPIN:
    :cvar SPIN_1:
    :cvar SPIN_NUTATION:
    :cvar SPIN_NUTATION_1:
    """

    QUATERNION = "quaternion"
    QUATERNION_1 = "QUATERNION"
    QUATERNION_DERIVATIVE = "quaternion/derivative"
    QUATERNION_DERIVATIVE_1 = "QUATERNION/DERIVATIVE"
    QUATERNION_RATE = "quaternion/rate"
    QUATERNION_RATE_1 = "QUATERNION/RATE"
    EULER_ANGLE = "euler_angle"
    EULER_ANGLE_1 = "EULER_ANGLE"
    EULER_ANGLE_RATE = "euler_angle/rate"
    EULER_ANGLE_RATE_1 = "EULER_ANGLE/RATE"
    SPIN = "spin"
    SPIN_1 = "SPIN"
    SPIN_NUTATION = "spin/nutation"
    SPIN_NUTATION_1 = "SPIN/NUTATION"


class QuaternionTypeType(Enum):
    """
    :cvar FIRST:
    :cvar FIRST_1:
    :cvar LAST:
    :cvar LAST_1:
    """

    FIRST = "first"
    FIRST_1 = "FIRST"
    LAST = "last"
    LAST_1 = "LAST"


@dataclass
class AemMetadata:
    """
    :ivar comment:
    :ivar object_name:
    :ivar object_id:
    :ivar center_name:
    :ivar ref_frame_a:
    :ivar ref_frame_b:
    :ivar attitude_dir:
    :ivar time_system:
    :ivar start_time:
    :ivar useable_start_time:
    :ivar useable_stop_time:
    :ivar stop_time:
    :ivar attitude_type:
    :ivar quaternion_type:
    :ivar euler_rot_seq:
    :ivar rate_frame:
    :ivar interpolation_method:
    :ivar interpolation_degree:
    """

    class Meta:
        name = "aemMetadata"

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
    ref_frame_a: Optional[str] = field(
        default=None,
        metadata={
            "name": "REF_FRAME_A",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    ref_frame_b: Optional[str] = field(
        default=None,
        metadata={
            "name": "REF_FRAME_B",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    attitude_dir: Optional[RotDirectionType] = field(
        default=None,
        metadata={
            "name": "ATTITUDE_DIR",
            "type": "Element",
            "namespace": "",
            "required": True,
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
    start_time: Optional[str] = field(
        default=None,
        metadata={
            "name": "START_TIME",
            "type": "Element",
            "namespace": "",
            "required": True,
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    useable_start_time: Optional[str] = field(
        default=None,
        metadata={
            "name": "USEABLE_START_TIME",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    useable_stop_time: Optional[str] = field(
        default=None,
        metadata={
            "name": "USEABLE_STOP_TIME",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    stop_time: Optional[str] = field(
        default=None,
        metadata={
            "name": "STOP_TIME",
            "type": "Element",
            "namespace": "",
            "required": True,
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    attitude_type: Optional[AttitudeTypeType] = field(
        default=None,
        metadata={
            "name": "ATTITUDE_TYPE",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    quaternion_type: Optional[QuaternionTypeType] = field(
        default=None,
        metadata={
            "name": "QUATERNION_TYPE",
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
    rate_frame: Optional[AemRateFrameType] = field(
        default=None,
        metadata={
            "name": "RATE_FRAME",
            "type": "Element",
            "namespace": "",
        },
    )
    interpolation_method: Optional[str] = field(
        default=None,
        metadata={
            "name": "INTERPOLATION_METHOD",
            "type": "Element",
            "namespace": "",
        },
    )
    interpolation_degree: Optional[int] = field(
        default=None,
        metadata={
            "name": "INTERPOLATION_DEGREE",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class EulerAngleRateType:
    """
    :ivar epoch:
    :ivar rotation_angles:
    :ivar rotation_rates:
    """

    class Meta:
        name = "eulerAngleRateType"

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
class EulerAngleType:
    """
    :ivar epoch:
    :ivar rotation_angles:
    """

    class Meta:
        name = "eulerAngleType"

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
    rotation_angles: Optional[RotationAngleType] = field(
        default=None,
        metadata={
            "name": "rotationAngles",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class QuaternionDerivativeType:
    """
    :ivar epoch:
    :ivar quaternion:
    :ivar quaternion_rate:
    """

    class Meta:
        name = "quaternionDerivativeType"

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
            "required": True,
        },
    )


@dataclass
class QuaternionEphemerisType:
    """
    :ivar epoch:
    :ivar quaternion:
    """

    class Meta:
        name = "quaternionEphemerisType"

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
    quaternion: Optional[QuaternionType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class QuaternionEulerRateType:
    """
    :ivar epoch:
    :ivar quaternion:
    :ivar rotation_rates:
    """

    class Meta:
        name = "quaternionEulerRateType"

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
    quaternion: Optional[QuaternionType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
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
class SpinNutationType:
    """
    :ivar epoch:
    :ivar spin_alpha:
    :ivar spin_delta:
    :ivar spin_angle:
    :ivar spin_angle_vel:
    :ivar nutation:
    :ivar nutation_per:
    :ivar nutation_phase:
    """

    class Meta:
        name = "spinNutationType"

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
    spin_alpha: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "SPIN_ALPHA",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    spin_delta: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "SPIN_DELTA",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    spin_angle: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "SPIN_ANGLE",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    spin_angle_vel: Optional[AngleRateType] = field(
        default=None,
        metadata={
            "name": "SPIN_ANGLE_VEL",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    nutation: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "NUTATION",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    nutation_per: Optional[DurationType] = field(
        default=None,
        metadata={
            "name": "NUTATION_PER",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    nutation_phase: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "NUTATION_PHASE",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class SpinType:
    """
    :ivar epoch:
    :ivar spin_alpha:
    :ivar spin_delta:
    :ivar spin_angle:
    :ivar spin_angle_vel:
    """

    class Meta:
        name = "spinType"

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
    spin_alpha: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "SPIN_ALPHA",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    spin_delta: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "SPIN_DELTA",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    spin_angle: Optional[AngleType] = field(
        default=None,
        metadata={
            "name": "SPIN_ANGLE",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    spin_angle_vel: Optional[AngleRateType] = field(
        default=None,
        metadata={
            "name": "SPIN_ANGLE_VEL",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class AttitudeStateType:
    """
    :ivar quaternion_state:
    :ivar quaternion_derivative:
    :ivar quaternion_euler_rate:
    :ivar euler_angle:
    :ivar euler_angle_rate:
    :ivar spin:
    :ivar spin_nutation:
    """

    class Meta:
        name = "attitudeStateType"

    quaternion_state: Optional[QuaternionEphemerisType] = field(
        default=None,
        metadata={
            "name": "quaternionState",
            "type": "Element",
            "namespace": "",
        },
    )
    quaternion_derivative: Optional[QuaternionDerivativeType] = field(
        default=None,
        metadata={
            "name": "quaternionDerivative",
            "type": "Element",
            "namespace": "",
        },
    )
    quaternion_euler_rate: Optional[QuaternionEulerRateType] = field(
        default=None,
        metadata={
            "name": "quaternionEulerRate",
            "type": "Element",
            "namespace": "",
        },
    )
    euler_angle: Optional[EulerAngleType] = field(
        default=None,
        metadata={
            "name": "eulerAngle",
            "type": "Element",
            "namespace": "",
        },
    )
    euler_angle_rate: Optional[EulerAngleRateType] = field(
        default=None,
        metadata={
            "name": "eulerAngleRate",
            "type": "Element",
            "namespace": "",
        },
    )
    spin: Optional[SpinType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )
    spin_nutation: Optional[SpinNutationType] = field(
        default=None,
        metadata={
            "name": "spinNutation",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class AemData:
    """
    :ivar comment:
    :ivar attitude_state:
    """

    class Meta:
        name = "aemData"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    attitude_state: List[AttitudeStateType] = field(
        default_factory=list,
        metadata={
            "name": "attitudeState",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        },
    )


@dataclass
class AemSegment:
    """
    :ivar metadata:
    :ivar data:
    """

    class Meta:
        name = "aemSegment"

    metadata: Optional[AemMetadata] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    data: Optional[AemData] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class AemBody:
    """
    :ivar segment:
    """

    class Meta:
        name = "aemBody"

    segment: List[AemSegment] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        },
    )


@dataclass
class AemType:
    """
    :ivar header:
    :ivar body:
    :ivar id:
    :ivar version:
    """

    class Meta:
        name = "aemType"

    header: Optional[NdmHeader] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    body: Optional[AemBody] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    id: str = field(
        init=False,
        default="CCSDS_AEM_VERS",
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
