from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional

__NAMESPACE__ = "urn:ccsds:recommendation:navigation:schema:ndmxml"


class AccUnits(Enum):
    """
    :cvar KM_S_2:
    """

    KM_S_2 = "km/s**2"


class AngleKeywordType(Enum):
    """
    :cvar X_ANGLE:
    :cvar Y_ANGLE:
    :cvar Z_ANGLE:
    """

    X_ANGLE = "X_ANGLE"
    Y_ANGLE = "Y_ANGLE"
    Z_ANGLE = "Z_ANGLE"


class AngleRateKeywordType(Enum):
    """
    :cvar X_RATE:
    :cvar Y_RATE:
    :cvar Z_RATE:
    """

    X_RATE = "X_RATE"
    Y_RATE = "Y_RATE"
    Z_RATE = "Z_RATE"


class AngleRateUnits(Enum):
    """
    :cvar DEG_S:
    """

    DEG_S = "deg/s"


class AngleUnits(Enum):
    """
    :cvar DEG:
    """

    DEG = "deg"


class AreaUnits(Enum):
    """
    :cvar M_2:
    """

    M_2 = "m**2"


class BallisticCoeffUnitsType(Enum):
    """
    :cvar KG_M_2:
    """

    KG_M_2 = "kg/m**2"


class ControlledType(Enum):
    """
    :cvar YES:
    :cvar YES_1:
    :cvar NO:
    :cvar NO_1:
    :cvar UNKNOWN:
    :cvar UNKNOWN_1:
    """

    YES = "YES"
    YES_1 = "yes"
    NO = "NO"
    NO_1 = "no"
    UNKNOWN = "UNKNOWN"
    UNKNOWN_1 = "unknown"


class DayIntervalUnits(Enum):
    """
    :cvar D:
    """

    D = "d"


class DisintegrationType(Enum):
    """
    :cvar NONE_VALUE:
    :cvar MASS_LOSS:
    :cvar BREAK_UP:
    :cvar MASS_LOSS_BREAK_UP:
    """

    NONE_VALUE = "NONE"
    MASS_LOSS = "MASS-LOSS"
    BREAK_UP = "BREAK-UP"
    MASS_LOSS_BREAK_UP = "MASS-LOSS + BREAK-UP"


class FrequencyUnits(Enum):
    """
    :cvar HZ:
    """

    HZ = "Hz"


class GmUnits(Enum):
    """
    :cvar KM_3_S_2:
    :cvar KM_3_S_2_1:
    """

    KM_3_S_2 = "km**3/s**2"
    KM_3_S_2_1 = "KM**3/S**2"


class ImpactUncertaintyType(Enum):
    """
    :cvar NONE_VALUE:
    :cvar ANALYTICAL:
    :cvar STOCHASTIC:
    :cvar EMPIRICAL:
    """

    NONE_VALUE = "NONE"
    ANALYTICAL = "ANALYTICAL"
    STOCHASTIC = "STOCHASTIC"
    EMPIRICAL = "EMPIRICAL"


class Km2Units(Enum):
    """
    :cvar KM_2:
    """

    KM_2 = "km**2"


class Km2S2Units(Enum):
    """
    :cvar KM_2_S_2:
    """

    KM_2_S_2 = "km**2/s**2"


class Km2SUnits(Enum):
    """
    :cvar KM_2_S:
    """

    KM_2_S = "km**2/s"


class LatLonUnits(Enum):
    """
    :cvar DEG:
    """

    DEG = "deg"


class LengthUnits(Enum):
    """
    :cvar M:
    """

    M = "m"


class MassUnits(Enum):
    """
    :cvar KG:
    """

    KG = "kg"


class MomentUnits(Enum):
    """
    :cvar KG_M_2:
    """

    KG_M_2 = "kg*m**2"


class Ms2Units(Enum):
    """
    :cvar M_S_2:
    """

    M_S_2 = "m/s**2"


@dataclass
class NdmHeader:
    """
    :ivar comment:
    :ivar creation_date:
    :ivar originator:
    """

    class Meta:
        name = "ndmHeader"

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


class ObjectDescriptionType(Enum):
    """
    :cvar PAYLOAD:
    :cvar PAYLOAD_1:
    :cvar ROCKET_BODY:
    :cvar ROCKET_BODY_1:
    :cvar UPPER_STAGE:
    :cvar UPPER_STAGE_1:
    :cvar DEBRIS:
    :cvar DEBRIS_1:
    :cvar UNKNOWN:
    :cvar UNKNOWN_1:
    :cvar OTHER:
    :cvar OTHER_1:
    """

    PAYLOAD = "PAYLOAD"
    PAYLOAD_1 = "payload"
    ROCKET_BODY = "ROCKET BODY"
    ROCKET_BODY_1 = "rocket body"
    UPPER_STAGE = "UPPER STAGE"
    UPPER_STAGE_1 = "upper stage"
    DEBRIS = "DEBRIS"
    DEBRIS_1 = "debris"
    UNKNOWN = "UNKNOWN"
    UNKNOWN_1 = "unknown"
    OTHER = "OTHER"
    OTHER_1 = "other"


@dataclass
class OemCovarianceMatrixAbstractType:
    """
    :ivar comment:
    :ivar epoch:
    :ivar cov_ref_frame:
    """

    class Meta:
        name = "oemCovarianceMatrixAbstractType"

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
    cov_ref_frame: Optional[str] = field(
        default=None,
        metadata={
            "name": "COV_REF_FRAME",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class OpmCovarianceMatrixAbstractType:
    """
    :ivar comment:
    :ivar cov_ref_frame:
    """

    class Meta:
        name = "opmCovarianceMatrixAbstractType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    cov_ref_frame: Optional[str] = field(
        default=None,
        metadata={
            "name": "COV_REF_FRAME",
            "type": "Element",
            "namespace": "",
        },
    )


class PercentageUnits(Enum):
    """
    :cvar VALUE:
    """

    VALUE = "%"


class PositionCovarianceUnits(Enum):
    """
    :cvar KM_2:
    """

    KM_2 = "km**2"


class PositionUnits(Enum):
    """
    :cvar KM:
    """

    KM = "km"


class PositionVelocityCovarianceUnits(Enum):
    """
    :cvar KM_2_S:
    """

    KM_2_S = "km**2/s"


class QuaternionDotUnits(Enum):
    """
    :cvar VALUE_1_S:
    """

    VALUE_1_S = "1/s"


@dataclass
class QuaternionType:
    """
    :ivar qc:
    :ivar q1:
    :ivar q2:
    :ivar q3:
    """

    class Meta:
        name = "quaternionType"

    qc: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "QC",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": -1.0,
            "max_inclusive": 1.0,
        },
    )
    q1: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Q1",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": -1.0,
            "max_inclusive": 1.0,
        },
    )
    q2: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Q2",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": -1.0,
            "max_inclusive": 1.0,
        },
    )
    q3: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Q3",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": -1.0,
            "max_inclusive": 1.0,
        },
    )


class ReentryUncertaintyMethodType(Enum):
    """
    :cvar NONE_VALUE:
    :cvar ANALYTICAL:
    :cvar STOCHASTIC:
    :cvar EMPIRICAL:
    """

    NONE_VALUE = "NONE"
    ANALYTICAL = "ANALYTICAL"
    STOCHASTIC = "STOCHASTIC"
    EMPIRICAL = "EMPIRICAL"


class RotDirectionType(Enum):
    """
    :cvar A2_B:
    :cvar B2_A:
    """

    A2_B = "A2B"
    B2_A = "B2A"


class RotseqType(Enum):
    """
    :cvar VALUE_121:
    :cvar VALUE_123:
    :cvar VALUE_131:
    :cvar VALUE_132:
    :cvar VALUE_212:
    :cvar VALUE_213:
    :cvar VALUE_231:
    :cvar VALUE_232:
    :cvar VALUE_312:
    :cvar VALUE_313:
    :cvar VALUE_321:
    :cvar VALUE_323:
    """

    VALUE_121 = "121"
    VALUE_123 = "123"
    VALUE_131 = "131"
    VALUE_132 = "132"
    VALUE_212 = "212"
    VALUE_213 = "213"
    VALUE_231 = "231"
    VALUE_232 = "232"
    VALUE_312 = "312"
    VALUE_313 = "313"
    VALUE_321 = "321"
    VALUE_323 = "323"


class TimeSystemType(Enum):
    """
    :cvar GMST:
    :cvar GMST_1:
    :cvar GPS:
    :cvar GPS_1:
    :cvar SCLK:
    :cvar SCLK_1:
    :cvar TAI:
    :cvar TAI_1:
    :cvar TCB:
    :cvar TCB_1:
    :cvar TDB:
    :cvar TDB_1:
    :cvar TOD:
    :cvar TOD_1:
    :cvar TT:
    :cvar TT_1:
    :cvar UT1:
    :cvar UT1_1:
    :cvar UTC:
    :cvar UTC_1:
    """

    GMST = "GMST"
    GMST_1 = "gmst"
    GPS = "GPS"
    GPS_1 = "gps"
    SCLK = "SCLK"
    SCLK_1 = "sclk"
    TAI = "TAI"
    TAI_1 = "tai"
    TCB = "TCB"
    TCB_1 = "tcb"
    TDB = "TDB"
    TDB_1 = "tdb"
    TOD = "TOD"
    TOD_1 = "tod"
    TT = "TT"
    TT_1 = "tt"
    UT1 = "UT1"
    UT1_1 = "ut1"
    UTC = "UTC"
    UTC_1 = "utc"


class TimeUnits(Enum):
    """
    :cvar S:
    """

    S = "s"


@dataclass
class UserDefinedParameterType:
    """
    :ivar value:
    :ivar parameter:
    """

    class Meta:
        name = "userDefinedParameterType"

    value: Optional[str] = field(
        default=None,
    )
    parameter: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


class VelocityCovarianceUnits(Enum):
    """
    :cvar KM_2_S_2:
    """

    KM_2_S_2 = "km**2/s**2"


class VelocityUnits(Enum):
    """
    :cvar KM_S:
    """

    KM_S = "km/s"


class YesNoType(Enum):
    """
    :cvar YES:
    :cvar YES_1:
    :cvar NO:
    :cvar NO_1:
    """

    YES = "YES"
    YES_1 = "yes"
    NO = "NO"
    NO_1 = "no"


@dataclass
class AccType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "accType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[AccUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AltType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "altType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": -430.5,
            "max_inclusive": 8848,
        },
    )
    units: Optional[LengthUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AngleRateType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "angleRateType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[AngleRateUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AngleType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "angleType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": -180.0,
            "max_exclusive": 360.0,
        },
    )
    units: Optional[AngleUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AreaType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "areaType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": 0.0,
        },
    )
    units: Optional[AreaUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class BallisticCoeffType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "ballisticCoeffType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": 0.0,
        },
    )
    units: Optional[BallisticCoeffUnitsType] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DayIntervalType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "dayIntervalType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_exclusive": 0.0,
        },
    )
    units: Optional[DayIntervalUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class DeltamassType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "deltamassType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "max_exclusive": 0.0,
        },
    )
    units: Optional[MassUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DistanceType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "distanceType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[PositionUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DurationType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "durationType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": 0.0,
        },
    )
    units: Optional[TimeUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class FrequencyType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "frequencyType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_exclusive": 0.0,
        },
    )
    units: Optional[FrequencyUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class GmType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "gmType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_exclusive": 0.0,
        },
    )
    units: Optional[GmUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class InclinationType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "inclinationType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": 0.0,
            "max_exclusive": 360.0,
            "max_inclusive": 180.0,
        },
    )
    units: Optional[AngleUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class Km2Type:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "km2Type"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[Km2Units] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class Km2S2Type:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "km2s2Type"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[Km2S2Units] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class Km2SType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "km2sType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[Km2SUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class LatType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "latType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": -90.0,
            "max_inclusive": 90.0,
        },
    )
    units: Optional[LatLonUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class LengthType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "lengthType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[LengthUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class LonType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "lonType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": -180.0,
            "max_inclusive": 180.0,
        },
    )
    units: Optional[LatLonUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class MassType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "massType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": 0.0,
        },
    )
    units: Optional[MassUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class MomentType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "momentType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[MomentUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class Ms2Type:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "ms2Type"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[Ms2Units] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class PercentageType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "percentageType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": 0.0,
            "max_inclusive": 100.0,
        },
    )
    units: Optional[PercentageUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class PositionCovarianceType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "positionCovarianceType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[PositionCovarianceUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class PositionType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "positionType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[PositionUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class PositionVelocityCovarianceType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "positionVelocityCovarianceType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[PositionVelocityCovarianceUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class QuaternionDotType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "quaternionDotType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[QuaternionDotUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class RdmPositionType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "rdmPositionType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[PositionUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class RdmVelocityType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "rdmVelocityType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[VelocityUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class RotationAngleComponentType:
    """
    :ivar value:
    :ivar angle:
    :ivar units:
    """

    class Meta:
        name = "rotationAngleComponentType"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "min_inclusive": -180.0,
            "max_exclusive": 360.0,
        },
    )
    angle: Optional[AngleKeywordType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    units: Optional[AngleUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class RotationAngleComponentTypeold:
    """
    :ivar units:
    :ivar angle:
    :ivar value:
    """

    class Meta:
        name = "rotationAngleComponentTypeold"

    units: Optional[AngleUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    angle: Optional[AngleKeywordType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
            "min_inclusive": -180.0,
            "max_exclusive": 360.0,
        },
    )


@dataclass
class RotationRateComponentType:
    """
    :ivar value:
    :ivar rate:
    :ivar units:
    """

    class Meta:
        name = "rotationRateComponentType"

    value: Optional[Decimal] = field(
        default=None,
    )
    rate: Optional[AngleRateKeywordType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    units: Optional[AngleRateUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class RotationRateComponentTypeOld:
    """
    :ivar units:
    :ivar rate:
    :ivar value:
    """

    class Meta:
        name = "rotationRateComponentTypeOLD"

    units: Optional[AngleRateUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    rate: Optional[AngleRateKeywordType] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class UserDefinedType:
    """
    :ivar comment:
    :ivar user_defined:
    """

    class Meta:
        name = "userDefinedType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
            "sequential": True,
        },
    )
    user_defined: List[UserDefinedParameterType] = field(
        default_factory=list,
        metadata={
            "name": "USER_DEFINED",
            "type": "Element",
            "namespace": "",
            "sequential": True,
        },
    )


@dataclass
class VelocityCovarianceType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "velocityCovarianceType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[VelocityCovarianceUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class VelocityType:
    """
    :ivar value:
    :ivar units:
    """

    class Meta:
        name = "velocityType"

    value: Optional[Decimal] = field(
        default=None,
    )
    units: Optional[VelocityUnits] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AtmosphericReentryParametersType:
    """
    :ivar comment:
    :ivar orbit_lifetime:
    :ivar reentry_altitude:
    :ivar orbit_lifetime_window_start:
    :ivar orbit_lifetime_window_end:
    :ivar nominal_reentry_epoch:
    :ivar reentry_window_start:
    :ivar reentry_window_end:
    :ivar orbit_lifetime_confidence_level:
    """

    class Meta:
        name = "atmosphericReentryParametersType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    orbit_lifetime: Optional[DayIntervalType] = field(
        default=None,
        metadata={
            "name": "ORBIT_LIFETIME",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    reentry_altitude: Optional[PositionType] = field(
        default=None,
        metadata={
            "name": "REENTRY_ALTITUDE",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    orbit_lifetime_window_start: Optional[DayIntervalType] = field(
        default=None,
        metadata={
            "name": "ORBIT_LIFETIME_WINDOW_START",
            "type": "Element",
            "namespace": "",
        },
    )
    orbit_lifetime_window_end: Optional[DayIntervalType] = field(
        default=None,
        metadata={
            "name": "ORBIT_LIFETIME_WINDOW_END",
            "type": "Element",
            "namespace": "",
        },
    )
    nominal_reentry_epoch: Optional[str] = field(
        default=None,
        metadata={
            "name": "NOMINAL_REENTRY_EPOCH",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    reentry_window_start: Optional[str] = field(
        default=None,
        metadata={
            "name": "REENTRY_WINDOW_START",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    reentry_window_end: Optional[str] = field(
        default=None,
        metadata={
            "name": "REENTRY_WINDOW_END",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    orbit_lifetime_confidence_level: Optional[PercentageType] = field(
        default=None,
        metadata={
            "name": "ORBIT_LIFETIME_CONFIDENCE_LEVEL",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class GroundImpactParametersType:
    """
    :ivar comment:
    :ivar probability_of_impact:
    :ivar probability_of_burn_up:
    :ivar probability_of_break_up:
    :ivar probability_of_land_impact:
    :ivar probability_of_casualty:
    :ivar nominal_impact_epoch:
    :ivar impact_window_start:
    :ivar impact_window_end:
    :ivar impact_ref_frame:
    :ivar nominal_impact_lon:
    :ivar nominal_impact_lat:
    :ivar nominal_impact_alt:
    :ivar impact_1_confidence:
    :ivar impact_1_start_lon:
    :ivar impact_1_start_lat:
    :ivar impact_1_stop_lon:
    :ivar impact_1_stop_lat:
    :ivar impact_1_cross_track:
    :ivar impact_2_confidence:
    :ivar impact_2_start_lon:
    :ivar impact_2_start_lat:
    :ivar impact_2_stop_lon:
    :ivar impact_2_stop_lat:
    :ivar impact_2_cross_track:
    :ivar impact_3_confidence:
    :ivar impact_3_start_lon:
    :ivar impact_3_start_lat:
    :ivar impact_3_stop_lon:
    :ivar impact_3_stop_lat:
    :ivar impact_3_cross_track:
    """

    class Meta:
        name = "groundImpactParametersType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    probability_of_impact: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "PROBABILITY_OF_IMPACT",
            "type": "Element",
            "namespace": "",
            "min_inclusive": 0.0,
            "max_inclusive": 1.0,
        },
    )
    probability_of_burn_up: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "PROBABILITY_OF_BURN_UP",
            "type": "Element",
            "namespace": "",
            "min_inclusive": 0.0,
            "max_inclusive": 1.0,
        },
    )
    probability_of_break_up: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "PROBABILITY_OF_BREAK_UP",
            "type": "Element",
            "namespace": "",
            "min_inclusive": 0.0,
            "max_inclusive": 1.0,
        },
    )
    probability_of_land_impact: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "PROBABILITY_OF_LAND_IMPACT",
            "type": "Element",
            "namespace": "",
            "min_inclusive": 0.0,
            "max_inclusive": 1.0,
        },
    )
    probability_of_casualty: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "PROBABILITY_OF_CASUALTY",
            "type": "Element",
            "namespace": "",
            "min_inclusive": 0.0,
            "max_inclusive": 1.0,
        },
    )
    nominal_impact_epoch: Optional[str] = field(
        default=None,
        metadata={
            "name": "NOMINAL_IMPACT_EPOCH",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    impact_window_start: Optional[str] = field(
        default=None,
        metadata={
            "name": "IMPACT_WINDOW_START",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    impact_window_end: Optional[str] = field(
        default=None,
        metadata={
            "name": "IMPACT_WINDOW_END",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    impact_ref_frame: Optional[str] = field(
        default=None,
        metadata={
            "name": "IMPACT_REF_FRAME",
            "type": "Element",
            "namespace": "",
        },
    )
    nominal_impact_lon: Optional[LonType] = field(
        default=None,
        metadata={
            "name": "NOMINAL_IMPACT_LON",
            "type": "Element",
            "namespace": "",
        },
    )
    nominal_impact_lat: Optional[LatType] = field(
        default=None,
        metadata={
            "name": "NOMINAL_IMPACT_LAT",
            "type": "Element",
            "namespace": "",
        },
    )
    nominal_impact_alt: Optional[AltType] = field(
        default=None,
        metadata={
            "name": "NOMINAL_IMPACT_ALT",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_1_confidence: Optional[PercentageType] = field(
        default=None,
        metadata={
            "name": "IMPACT_1_CONFIDENCE",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_1_start_lon: Optional[LonType] = field(
        default=None,
        metadata={
            "name": "IMPACT_1_START_LON",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_1_start_lat: Optional[LatType] = field(
        default=None,
        metadata={
            "name": "IMPACT_1_START_LAT",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_1_stop_lon: Optional[LonType] = field(
        default=None,
        metadata={
            "name": "IMPACT_1_STOP_LON",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_1_stop_lat: Optional[LatType] = field(
        default=None,
        metadata={
            "name": "IMPACT_1_STOP_LAT",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_1_cross_track: Optional[DistanceType] = field(
        default=None,
        metadata={
            "name": "IMPACT_1_CROSS_TRACK",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_2_confidence: Optional[PercentageType] = field(
        default=None,
        metadata={
            "name": "IMPACT_2_CONFIDENCE",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_2_start_lon: Optional[LonType] = field(
        default=None,
        metadata={
            "name": "IMPACT_2_START_LON",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_2_start_lat: Optional[LatType] = field(
        default=None,
        metadata={
            "name": "IMPACT_2_START_LAT",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_2_stop_lon: Optional[LonType] = field(
        default=None,
        metadata={
            "name": "IMPACT_2_STOP_LON",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_2_stop_lat: Optional[LatType] = field(
        default=None,
        metadata={
            "name": "IMPACT_2_STOP_LAT",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_2_cross_track: Optional[DistanceType] = field(
        default=None,
        metadata={
            "name": "IMPACT_2_CROSS_TRACK",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_3_confidence: Optional[PercentageType] = field(
        default=None,
        metadata={
            "name": "IMPACT_3_CONFIDENCE",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_3_start_lon: Optional[LonType] = field(
        default=None,
        metadata={
            "name": "IMPACT_3_START_LON",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_3_start_lat: Optional[LatType] = field(
        default=None,
        metadata={
            "name": "IMPACT_3_START_LAT",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_3_stop_lon: Optional[LonType] = field(
        default=None,
        metadata={
            "name": "IMPACT_3_STOP_LON",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_3_stop_lat: Optional[LatType] = field(
        default=None,
        metadata={
            "name": "IMPACT_3_STOP_LAT",
            "type": "Element",
            "namespace": "",
        },
    )
    impact_3_cross_track: Optional[DistanceType] = field(
        default=None,
        metadata={
            "name": "IMPACT_3_CROSS_TRACK",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class OdParametersType:
    """
    :ivar comment:
    :ivar time_lastob_start:
    :ivar time_lastob_end:
    :ivar recommended_od_span:
    :ivar actual_od_span:
    :ivar obs_available:
    :ivar obs_used:
    :ivar tracks_available:
    :ivar tracks_used:
    :ivar residuals_accepted:
    :ivar weighted_rms:
    """

    class Meta:
        name = "odParametersType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    time_lastob_start: Optional[str] = field(
        default=None,
        metadata={
            "name": "TIME_LASTOB_START",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    time_lastob_end: Optional[str] = field(
        default=None,
        metadata={
            "name": "TIME_LASTOB_END",
            "type": "Element",
            "namespace": "",
            "pattern": r"\-?\d{4}\d*-((\d{2}\-\d{2})|\d{3})T\d{2}:\d{2}:\d{2}(\.\d*)?(Z|[+|\-]\d{2}:\d{2})?|[+|\-]?\d*(\.\d*)?",
        },
    )
    recommended_od_span: Optional[DayIntervalType] = field(
        default=None,
        metadata={
            "name": "RECOMMENDED_OD_SPAN",
            "type": "Element",
            "namespace": "",
        },
    )
    actual_od_span: Optional[DayIntervalType] = field(
        default=None,
        metadata={
            "name": "ACTUAL_OD_SPAN",
            "type": "Element",
            "namespace": "",
        },
    )
    obs_available: Optional[int] = field(
        default=None,
        metadata={
            "name": "OBS_AVAILABLE",
            "type": "Element",
            "namespace": "",
        },
    )
    obs_used: Optional[int] = field(
        default=None,
        metadata={
            "name": "OBS_USED",
            "type": "Element",
            "namespace": "",
        },
    )
    tracks_available: Optional[int] = field(
        default=None,
        metadata={
            "name": "TRACKS_AVAILABLE",
            "type": "Element",
            "namespace": "",
        },
    )
    tracks_used: Optional[int] = field(
        default=None,
        metadata={
            "name": "TRACKS_USED",
            "type": "Element",
            "namespace": "",
        },
    )
    residuals_accepted: Optional[PercentageType] = field(
        default=None,
        metadata={
            "name": "RESIDUALS_ACCEPTED",
            "type": "Element",
            "namespace": "",
        },
    )
    weighted_rms: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "WEIGHTED_RMS",
            "type": "Element",
            "namespace": "",
            "min_inclusive": 0.0,
        },
    )


@dataclass
class OemCovarianceMatrixType(OemCovarianceMatrixAbstractType):
    """
    :ivar cx_x:
    :ivar cy_x:
    :ivar cy_y:
    :ivar cz_x:
    :ivar cz_y:
    :ivar cz_z:
    :ivar cx_dot_x:
    :ivar cx_dot_y:
    :ivar cx_dot_z:
    :ivar cx_dot_x_dot:
    :ivar cy_dot_x:
    :ivar cy_dot_y:
    :ivar cy_dot_z:
    :ivar cy_dot_x_dot:
    :ivar cy_dot_y_dot:
    :ivar cz_dot_x:
    :ivar cz_dot_y:
    :ivar cz_dot_z:
    :ivar cz_dot_x_dot:
    :ivar cz_dot_y_dot:
    :ivar cz_dot_z_dot:
    """

    class Meta:
        name = "oemCovarianceMatrixType"

    cx_x: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CX_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_x: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_y: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_x: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_y: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_z: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_Z",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cx_dot_x: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CX_DOT_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cx_dot_y: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CX_DOT_Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cx_dot_z: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CX_DOT_Z",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cx_dot_x_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CX_DOT_X_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_dot_x: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_DOT_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_dot_y: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_DOT_Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_dot_z: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_DOT_Z",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_dot_x_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_DOT_X_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_dot_y_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_DOT_Y_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_x: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_y: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_z: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_Z",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_x_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_X_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_y_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_Y_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_z_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_Z_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class OpmCovarianceMatrixType(OpmCovarianceMatrixAbstractType):
    """
    :ivar cx_x:
    :ivar cy_x:
    :ivar cy_y:
    :ivar cz_x:
    :ivar cz_y:
    :ivar cz_z:
    :ivar cx_dot_x:
    :ivar cx_dot_y:
    :ivar cx_dot_z:
    :ivar cx_dot_x_dot:
    :ivar cy_dot_x:
    :ivar cy_dot_y:
    :ivar cy_dot_z:
    :ivar cy_dot_x_dot:
    :ivar cy_dot_y_dot:
    :ivar cz_dot_x:
    :ivar cz_dot_y:
    :ivar cz_dot_z:
    :ivar cz_dot_x_dot:
    :ivar cz_dot_y_dot:
    :ivar cz_dot_z_dot:
    """

    class Meta:
        name = "opmCovarianceMatrixType"

    cx_x: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CX_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_x: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_y: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_x: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_y: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_z: Optional[PositionCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_Z",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cx_dot_x: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CX_DOT_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cx_dot_y: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CX_DOT_Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cx_dot_z: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CX_DOT_Z",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cx_dot_x_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CX_DOT_X_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_dot_x: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_DOT_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_dot_y: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_DOT_Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_dot_z: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_DOT_Z",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_dot_x_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_DOT_X_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cy_dot_y_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CY_DOT_Y_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_x: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_y: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_z: Optional[PositionVelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_Z",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_x_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_X_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_y_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_Y_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    cz_dot_z_dot: Optional[VelocityCovarianceType] = field(
        default=None,
        metadata={
            "name": "CZ_DOT_Z_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class QuaternionRateType:
    """
    :ivar qc_dot:
    :ivar q1_dot:
    :ivar q2_dot:
    :ivar q3_dot:
    """

    class Meta:
        name = "quaternionRateType"

    qc_dot: Optional[QuaternionDotType] = field(
        default=None,
        metadata={
            "name": "QC_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    q1_dot: Optional[QuaternionDotType] = field(
        default=None,
        metadata={
            "name": "Q1_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    q2_dot: Optional[QuaternionDotType] = field(
        default=None,
        metadata={
            "name": "Q2_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    q3_dot: Optional[QuaternionDotType] = field(
        default=None,
        metadata={
            "name": "Q3_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class RdmSpacecraftParametersType:
    """
    :ivar comment:
    :ivar wet_mass:
    :ivar dry_mass:
    :ivar hazardous_substances:
    :ivar solar_rad_area:
    :ivar solar_rad_coeff:
    :ivar drag_area:
    :ivar drag_coeff:
    :ivar rcs:
    :ivar ballistic_coeff:
    :ivar thrust_acceleration:
    """

    class Meta:
        name = "rdmSpacecraftParametersType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    wet_mass: Optional[MassType] = field(
        default=None,
        metadata={
            "name": "WET_MASS",
            "type": "Element",
            "namespace": "",
        },
    )
    dry_mass: Optional[MassType] = field(
        default=None,
        metadata={
            "name": "DRY_MASS",
            "type": "Element",
            "namespace": "",
        },
    )
    hazardous_substances: Optional[str] = field(
        default=None,
        metadata={
            "name": "HAZARDOUS_SUBSTANCES",
            "type": "Element",
            "namespace": "",
        },
    )
    solar_rad_area: Optional[AreaType] = field(
        default=None,
        metadata={
            "name": "SOLAR_RAD_AREA",
            "type": "Element",
            "namespace": "",
        },
    )
    solar_rad_coeff: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "SOLAR_RAD_COEFF",
            "type": "Element",
            "namespace": "",
            "min_inclusive": 0.0,
        },
    )
    drag_area: Optional[AreaType] = field(
        default=None,
        metadata={
            "name": "DRAG_AREA",
            "type": "Element",
            "namespace": "",
        },
    )
    drag_coeff: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "DRAG_COEFF",
            "type": "Element",
            "namespace": "",
            "min_inclusive": 0.0,
        },
    )
    rcs: Optional[AreaType] = field(
        default=None,
        metadata={
            "name": "RCS",
            "type": "Element",
            "namespace": "",
        },
    )
    ballistic_coeff: Optional[BallisticCoeffType] = field(
        default=None,
        metadata={
            "name": "BALLISTIC_COEFF",
            "type": "Element",
            "namespace": "",
        },
    )
    thrust_acceleration: Optional[Ms2Type] = field(
        default=None,
        metadata={
            "name": "THRUST_ACCELERATION",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class RotationAngleType:
    """
    :ivar rotation1:
    :ivar rotation2:
    :ivar rotation3:
    """

    class Meta:
        name = "rotationAngleType"

    rotation1: Optional[RotationAngleComponentType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    rotation2: Optional[RotationAngleComponentType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    rotation3: Optional[RotationAngleComponentType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class RotationRateType:
    """
    :ivar rotation1:
    :ivar rotation2:
    :ivar rotation3:
    """

    class Meta:
        name = "rotationRateType"

    rotation1: Optional[RotationRateComponentType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    rotation2: Optional[RotationRateComponentType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    rotation3: Optional[RotationRateComponentType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class SpacecraftParametersType:
    """
    :ivar comment:
    :ivar mass:
    :ivar solar_rad_area:
    :ivar solar_rad_coeff:
    :ivar drag_area:
    :ivar drag_coeff:
    """

    class Meta:
        name = "spacecraftParametersType"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    mass: Optional[MassType] = field(
        default=None,
        metadata={
            "name": "MASS",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    solar_rad_area: Optional[AreaType] = field(
        default=None,
        metadata={
            "name": "SOLAR_RAD_AREA",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    solar_rad_coeff: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "SOLAR_RAD_COEFF",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": 0.0,
        },
    )
    drag_area: Optional[AreaType] = field(
        default=None,
        metadata={
            "name": "DRAG_AREA",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    drag_coeff: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "DRAG_COEFF",
            "type": "Element",
            "namespace": "",
            "required": True,
            "min_inclusive": 0.0,
        },
    )


@dataclass
class StateVectorAccType:
    """
    :ivar epoch:
    :ivar x:
    :ivar y:
    :ivar z:
    :ivar x_dot:
    :ivar y_dot:
    :ivar z_dot:
    :ivar x_ddot:
    :ivar y_ddot:
    :ivar z_ddot:
    """

    class Meta:
        name = "stateVectorAccType"

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
    x: Optional[PositionType] = field(
        default=None,
        metadata={
            "name": "X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    y: Optional[PositionType] = field(
        default=None,
        metadata={
            "name": "Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    z: Optional[PositionType] = field(
        default=None,
        metadata={
            "name": "Z",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    x_dot: Optional[VelocityType] = field(
        default=None,
        metadata={
            "name": "X_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    y_dot: Optional[VelocityType] = field(
        default=None,
        metadata={
            "name": "Y_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    z_dot: Optional[VelocityType] = field(
        default=None,
        metadata={
            "name": "Z_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    x_ddot: Optional[AccType] = field(
        default=None,
        metadata={
            "name": "X_DDOT",
            "type": "Element",
            "namespace": "",
        },
    )
    y_ddot: Optional[AccType] = field(
        default=None,
        metadata={
            "name": "Y_DDOT",
            "type": "Element",
            "namespace": "",
        },
    )
    z_ddot: Optional[AccType] = field(
        default=None,
        metadata={
            "name": "Z_DDOT",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class StateVectorType:
    """
    :ivar comment:
    :ivar epoch:
    :ivar x:
    :ivar y:
    :ivar z:
    :ivar x_dot:
    :ivar y_dot:
    :ivar z_dot:
    """

    class Meta:
        name = "stateVectorType"

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
    x: Optional[PositionType] = field(
        default=None,
        metadata={
            "name": "X",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    y: Optional[PositionType] = field(
        default=None,
        metadata={
            "name": "Y",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    z: Optional[PositionType] = field(
        default=None,
        metadata={
            "name": "Z",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    x_dot: Optional[VelocityType] = field(
        default=None,
        metadata={
            "name": "X_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    y_dot: Optional[VelocityType] = field(
        default=None,
        metadata={
            "name": "Y_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    z_dot: Optional[VelocityType] = field(
        default=None,
        metadata={
            "name": "Z_DOT",
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
