from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from ccsds_ndm.models.ndmxml2.ndmxml_2_0_0_common_2_0 import (
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

__NAMESPACE__ = "urn:ccsds:schema:ndmxml"


class AemRateFrameType(Enum):
    REF_FRAME_A = "ref_frame_a"
    REF_FRAME_A_1 = "REF_FRAME_A"
    REF_FRAME_B = "ref_frame_b"
    REF_FRAME_B_1 = "REF_FRAME_B"


class AttitudeTypeType(Enum):
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
    FIRST = "first"
    FIRST_1 = "FIRST"
    LAST = "last"
    LAST_1 = "LAST"


@dataclass
class AemMetadata:
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
