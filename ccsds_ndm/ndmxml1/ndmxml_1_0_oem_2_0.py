from dataclasses import dataclass, field
from typing import List, Optional

from ccsds_ndm.ndmxml1.ndmxml_1_0_navwg_common import (
    NdmHeader,
    OemCovarianceMatrixType,
    StateVectorAccType,
)

__NAMESPACE__ = "urn:ccsds:recommendation:navigation:schema:ndmxml"


@dataclass
class OemMetadata:
    """
    :ivar comment:
    :ivar object_name:
    :ivar object_id:
    :ivar center_name:
    :ivar ref_frame:
    :ivar ref_frame_epoch:
    :ivar time_system:
    :ivar start_time:
    :ivar useable_start_time:
    :ivar useable_stop_time:
    :ivar stop_time:
    :ivar interpolation:
    :ivar interpolation_degree:
    """

    class Meta:
        name = "oemMetadata"

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
    interpolation: Optional[str] = field(
        default=None,
        metadata={
            "name": "INTERPOLATION",
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
class OemData:
    """
    :ivar comment:
    :ivar state_vector:
    :ivar covariance_matrix:
    """

    class Meta:
        name = "oemData"

    comment: List[str] = field(
        default_factory=list,
        metadata={
            "name": "COMMENT",
            "type": "Element",
            "namespace": "",
        },
    )
    state_vector: List[StateVectorAccType] = field(
        default_factory=list,
        metadata={
            "name": "stateVector",
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        },
    )
    covariance_matrix: List[OemCovarianceMatrixType] = field(
        default_factory=list,
        metadata={
            "name": "covarianceMatrix",
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class OemSegment:
    """
    :ivar metadata:
    :ivar data:
    """

    class Meta:
        name = "oemSegment"

    metadata: Optional[OemMetadata] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    data: Optional[OemData] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )


@dataclass
class OemBody:
    """
    :ivar segment:
    """

    class Meta:
        name = "oemBody"

    segment: List[OemSegment] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
            "min_occurs": 1,
        },
    )


@dataclass
class OemType:
    """
    :ivar header:
    :ivar body:
    :ivar id:
    :ivar version:
    """

    class Meta:
        name = "oemType"

    header: Optional[NdmHeader] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    body: Optional[OemBody] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "",
            "required": True,
        },
    )
    id: str = field(
        init=False,
        default="CCSDS_OEM_VERS",
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
