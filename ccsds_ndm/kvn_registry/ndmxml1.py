# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.
"""
KVN handler registry for the ndmxml 1.0 schema.

Maps xsdata class name (str) → TypeHandler and root class name → dispatch
strategy.  Classes absent from the registry implicitly use DEFAULT_HANDLER.

All-default types (no explicit entry needed)
--------------------------------------------
NdmHeader, OpmMetadata, OemMetadata, AemMetadata, OmmMetadata,
ApmMetadata, TdmMetadata, CdmMetadata,
StateVectorType (OPM — plain KEY=VALUE, not packed),
KeplerianElementsType, ManeuverParametersType,
SpacecraftParametersType, OdParametersType,
OpmCovarianceMatrixType (plain KEY=VALUE, no packed rows),
CdmCovarianceType (plain KEY=VALUE lower-triangular fields),
UserDefinedType, UserDefinedParameterType,
QuaternionType, QuaternionRateType,
QuaternionEphemerisType, QuaternionDerivativeType, QuaternionEulerRateType,
EulerAngleType, EulerAngleRateType,
SpinType, SpinNutationType,
and all scalar-with-units leaf types (PositionType, VelocityType, …).

Note: ndmxml1 classes share the same special handler types as ndmxml2 —
StateVectorAccType, AttitudeStateType, OemCovarianceMatrixType,
TrackingDataObservationType, RotationAngleType, and RotationRateType
are all defined in the ndmxml1 common module with identical KVN structure.
"""

from __future__ import annotations

from ccsds_ndm.kvn_handlers import (
    DEFAULT_HANDLER,
    DISPATCH_CDM,
    DISPATCH_FLAT,
    DISPATCH_SEGMENTED,
    LOC_COVARIANCE,
    LOC_DEFAULT,
    LOC_PACKED_ATTITUDE,
    LOC_PACKED_STATE,
    LOC_TDM_OBS,
    PARSE_COVARIANCE,
    PARSE_PACKED_ATTITUDE,
    PARSE_PACKED_STATE,
    PARSE_ROTATION_ANGLE,
    PARSE_ROTATION_RATE,
    PARSE_TDM_OBS,
    WRITE_COVARIANCE,
    WRITE_PACKED_ATTITUDE,
    WRITE_PACKED_STATE,
    WRITE_ROTATION_ANGLE,
    WRITE_ROTATION_RATE,
    WRITE_TDM_OBS,
    TypeHandler,
)


class NdmXml1Registry:
    """KVN handler registry for the ndmxml 1.0 schema."""

    def __init__(self) -> None:
        self.version: int = 1

        # NDM type ids that use segmented dispatch (META_START/STOP blocks)
        self.segmented_ids: frozenset[str] = frozenset({"aem", "oem", "tdm"})

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
            # -- APM Euler angle container: keyword from rotation.angle discriminator
            #    (X_ANGLE / Y_ANGLE / Z_ANGLE); locate is default (keywords are in kw set)
            "RotationAngleType": TypeHandler(
                locate=LOC_DEFAULT,
                parse=PARSE_ROTATION_ANGLE,
                write=WRITE_ROTATION_ANGLE,
            ),
            # -- APM Euler rate container: keyword from rotation.rate discriminator
            #    (X_RATE / Y_RATE / Z_RATE)
            "RotationRateType": TypeHandler(
                locate=LOC_DEFAULT,
                parse=PARSE_ROTATION_RATE,
                write=WRITE_ROTATION_RATE,
            ),
        }

        # Maps root class name → dispatch strategy sentinel
        self.dispatch: dict[str, str] = {
            # Flat: single segment, no META_START/STOP in KVN body
            "Opm": DISPATCH_FLAT,
            "Omm": DISPATCH_FLAT,
            "Apm": DISPATCH_FLAT,
            "Rdm": DISPATCH_FLAT,
            # Segmented: META_START/META_STOP/DATA_START/DATA_STOP state machine
            "Oem": DISPATCH_SEGMENTED,
            "Aem": DISPATCH_SEGMENTED,
            "Tdm": DISPATCH_SEGMENTED,
            # Special CDM structure
            "Cdm": DISPATCH_CDM,
        }

    def get_handler(self, cls_name: str) -> TypeHandler:
        """Return the TypeHandler for ``cls_name``, falling back to DEFAULT_HANDLER."""
        return self.registry.get(cls_name, DEFAULT_HANDLER)


# Module-level singleton
REGISTRY_INSTANCE = NdmXml1Registry()
