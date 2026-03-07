# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE.rst for more info.
"""
KVN handler registry for the ndmxml 4.0 schema.

Maps xsdata class name (str) → TypeHandler and root class name → dispatch
strategy.  Classes absent from the registry implicitly use DEFAULT_HANDLER.

All-default types (no explicit entry needed)
--------------------------------------------
NdmHeader, OpmMetadata, OemMetadata, AemMetadata, OmmMetadata,
ApmMetadata, TdmMetadata, CdmMetadata, AcmMetadata, OcmMetadata,
StateVectorType (OPM — plain KEY=VALUE, not packed),
KeplerianElementsType, ManeuverParametersType,
SpacecraftParametersType, OdParametersType,
OpmCovarianceMatrixType (plain KEY=VALUE, no packed rows),
CdmCovarianceMatrixType (plain KEY=VALUE lower-triangular fields),
OcmManeuverParametersType, OcmPerturbationsType,
OcmOdParametersType, OcmPhysicalDescriptionType,
AcmManeuverParametersType, AcmPhysicalDescriptionType,
AcmAdParametersType, SensorDataType,
UserDefinedType, UserDefinedParameterType,
QuaternionType, QuaternionStateType,
QuaternionEphemerisType, QuaternionDerivativeType,
EulerAngleType, EulerAngleStateType,
AngVelStateType, SpinStateType, InertiaStateType,
AttManeuverStateType,
SpinType, SpinNutationType,
and all scalar-with-units leaf types (PositionTypeUo, VelocityTypeUo, …).

Differences from ndmxml2
------------------------
- Adds two new message types: ``AcmType`` (flat) and ``OcmType`` (segmented).
- APM dropped ``RotationAngleType`` / ``RotationRateType`` — Euler angle state
  is now ``EulerAngleStateType`` (DEFAULT_HANDLER).
- OCM and ACM introduce a mixed block structure (KEY=VALUE header fields +
  a packed ``list[str]``) requiring ``LOC_PACKED_LINES`` / ``PARSE_PACKED_LINES``
  / ``WRITE_PACKED_LINES`` for ``OcmTrajStateType``, ``OcmCovarianceMatrixType``,
  ``AcmAttitudeStateType``, and ``AcmCovarianceMatrixType``.
- Scalar leaf types are split into ``*TypeUo`` / ``*TypeUr`` variants
  (e.g. ``PositionTypeUo``, ``VelocityTypeUo``) — all still DEFAULT_HANDLER.
- ``QuaternionRateType`` and ``QuaternionEulerRateType`` are absent; replaced
  by ``QuaternionAngVelType`` and ``EulerAngleAngVelType`` (DEFAULT_HANDLER).
"""

from __future__ import annotations

from ccsds_ndm.kvn_handlers import (
    DEFAULT_HANDLER,
    DISPATCH_CDM,
    DISPATCH_FLAT,
    DISPATCH_SEGMENTED,
    LOC_COVARIANCE,
    LOC_PACKED_ATTITUDE,
    LOC_PACKED_LINES,
    LOC_PACKED_STATE,
    LOC_TDM_OBS,
    PARSE_COVARIANCE,
    PARSE_PACKED_ATTITUDE,
    PARSE_PACKED_LINES,
    PARSE_PACKED_STATE,
    PARSE_TDM_OBS,
    WRITE_COVARIANCE,
    WRITE_PACKED_ATTITUDE,
    WRITE_PACKED_LINES,
    WRITE_PACKED_STATE,
    WRITE_TDM_OBS,
    TypeHandler,
)


class NdmXml4Registry:
    """KVN handler registry for the ndmxml 4.0 schema."""

    def __init__(self) -> None:
        self.version: int = 4

        # NDM type ids that use segmented dispatch (META_START/STOP blocks)
        self.segmented_ids: frozenset[str] = frozenset(
            {"aem", "acm", "oem", "ocm", "tdm"}
        )

        # NDM type ids that use CDM dispatch (split on OBJECT_1/OBJECT_2)
        self.cdm_ids: frozenset[str] = frozenset({"cdm"})

        # Maps xsdata class name → TypeHandler (absent → DEFAULT_HANDLER)
        self.registry: dict[str, TypeHandler] = {
            # -- OEM: packed epoch-led state vector rows
            "StateVectorAccType": TypeHandler(
                locate=LOC_PACKED_STATE,
                parse=PARSE_PACKED_STATE,
                write=WRITE_PACKED_STATE,
            ),
            # -- AEM: packed attitude rows (column template from ctx['meta'].attitude_type)
            "AttitudeStateType": TypeHandler(
                locate=LOC_PACKED_ATTITUDE,
                parse=PARSE_PACKED_ATTITUDE,
                write=WRITE_PACKED_ATTITUDE,
            ),
            # -- OEM covariance block (EPOCH line + lower-triangular numeric rows)
            "OemCovarianceMatrixType": TypeHandler(
                locate=LOC_COVARIANCE,
                parse=PARSE_COVARIANCE,
                write=WRITE_COVARIANCE,
            ),
            # -- TDM observation lines: KEY = EPOCH VALUE
            "TrackingDataObservationType": TypeHandler(
                locate=LOC_TDM_OBS,
                parse=PARSE_TDM_OBS,
                write=WRITE_TDM_OBS,
            ),
            # -- OCM trajectory state block: KEY=VALUE header + packed trajLine entries
            "OcmTrajStateType": TypeHandler(
                locate=LOC_PACKED_LINES,
                parse=PARSE_PACKED_LINES,
                write=WRITE_PACKED_LINES,
            ),
            # -- OCM covariance block: KEY=VALUE header + packed covLine entries
            "OcmCovarianceMatrixType": TypeHandler(
                locate=LOC_PACKED_LINES,
                parse=PARSE_PACKED_LINES,
                write=WRITE_PACKED_LINES,
            ),
            # -- ACM attitude state block: KEY=VALUE header + packed attLine entries
            "AcmAttitudeStateType": TypeHandler(
                locate=LOC_PACKED_LINES,
                parse=PARSE_PACKED_LINES,
                write=WRITE_PACKED_LINES,
            ),
            # -- ACM covariance block: KEY=VALUE header + packed covLine entries
            "AcmCovarianceMatrixType": TypeHandler(
                locate=LOC_PACKED_LINES,
                parse=PARSE_PACKED_LINES,
                write=WRITE_PACKED_LINES,
            ),
        }

        # Maps root class name → dispatch strategy sentinel
        self.dispatch: dict[str, str] = {
            # Flat: single segment, no META_START/STOP in KVN body
            "Opm": DISPATCH_FLAT,
            "Omm": DISPATCH_FLAT,
            "Apm": DISPATCH_FLAT,
            "Rdm": DISPATCH_FLAT,
            "Acm": DISPATCH_FLAT,
            # Segmented: META_START/META_STOP/DATA_START/DATA_STOP state machine
            "Oem": DISPATCH_SEGMENTED,
            "Aem": DISPATCH_SEGMENTED,
            "Tdm": DISPATCH_SEGMENTED,
            "Ocm": DISPATCH_SEGMENTED,
            # Special CDM structure
            "Cdm": DISPATCH_CDM,
        }

    def get_handler(self, cls_name: str) -> TypeHandler:
        """Return the TypeHandler for ``cls_name``, falling back to DEFAULT_HANDLER."""
        return self.registry.get(cls_name, DEFAULT_HANDLER)


# Module-level singleton
REGISTRY_INSTANCE = NdmXml4Registry()
