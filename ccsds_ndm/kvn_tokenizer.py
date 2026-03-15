# CCSDS-NDM: CCSDS Navigation Data Messages Read/Write Library
#
# Copyright (C) Egemen Imre
#
# Licensed under GNU GPL v3.0. See LICENSE for more info.
"""
KVN tokenizer: convert raw KVN text into a list of classified line objects.

This module provides:
  - :class:`KvnLine` and its subclasses for representing each line format
  - :func:`tokenize` to convert raw KVN source into ``KvnLine`` objects
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

_SECTION_MARKERS = frozenset(
    {
        "META_START",
        "META_STOP",
        "DATA_START",
        "DATA_STOP",
        "COVARIANCE_START",
        "COVARIANCE_STOP",
    }
)


@dataclass
class KvnLine(ABC):
    """
    Abstract base class for a single tokenised KVN line.

    Subclasses represent each distinct line format found in KVN files.
    Every subclass implements :meth:`to_str` to render itself back to a
    canonical KVN string, making round-trip writing straightforward: build a
    list of ``KvnLine`` instances, call ``to_str()`` on each, and join with
    newlines.
    """

    @abstractmethod
    def to_str(self, **kwargs) -> str:
        """
        Render this line to a KVN string (no trailing newline).

        Subclasses accept keyword arguments relevant to their own format.
        Unknown kwargs are silently ignored, so callers can pass a common set
        (e.g. ``key_width=24``) to all line types without special-casing.
        """


@dataclass
class BlankLine(KvnLine):
    """A whitespace-only (or completely empty) line."""

    def to_str(self, **kwargs) -> str:
        return ""


@dataclass
class SectionMarkerLine(KvnLine):
    """
    A block-delimiter keyword.

    Examples: ``META_START``, ``META_STOP``, ``DATA_START``, ``DATA_STOP``,
    ``COVARIANCE_START``, ``COVARIANCE_STOP``.
    """

    key: str = ""

    def to_str(self, **kwargs) -> str:
        return self.key


@dataclass
class CommentLine(KvnLine):
    """
    A ``COMMENT`` line.

    The comment text is stored in :attr:`text` with leading/trailing whitespace
    stripped.  Both the plain (``COMMENT text``) and equals (``COMMENT = text``)
    variants are normalised to plain on construction; ``to_str`` always writes
    the plain form.
    """

    text: str = ""

    def to_str(self, **kwargs) -> str:
        return f"COMMENT {self.text}"


@dataclass
class KvLine(KvnLine):
    """
    A standard ``KEY = value [unit]`` line.

    Attributes
    ----------
    key : str
        The KVN keyword (e.g. ``"EPOCH"``, ``"OBJECT_NAME"``).
    value : str
        The scalar value string, stripped of surrounding whitespace and units.
    unit : str
        Unit string extracted from the trailing ``[...]``, or empty if absent.
    """

    key: str = ""
    value: str = ""
    unit: str = ""

    def to_str(self, key_width: int = 24, **kwargs) -> str:

        unit_str = f" [{self.unit}]" if self.unit else ""
        return f"{self.key:<{key_width}} = {self.value}{unit_str}"


@dataclass
class TdmObsLine(KvnLine):
    """
    A TDM observation line: ``KEY = EPOCH  value``.

    TDM data lines carry an epoch and a numeric value in the value field,
    separated by whitespace, rather than a single scalar.

    Attributes
    ----------
    key : str
        The observation keyword (e.g. ``"TRANSMIT_FREQ_1"``).
    epoch : str
        The epoch token (e.g. ``"2007-075T11:50:43.000"``).
    value : str
        The numeric observation value as a string.
    unit : str
        Unit string, or empty if absent.
    """

    key: str = ""
    epoch: str = ""
    value: str = ""
    unit: str = ""

    def to_str(self, key_width: int = 24, **kwargs) -> str:
        unit_str = f" [{self.unit}]" if self.unit else ""
        return f"{self.key:<{key_width}} = {self.epoch}  {self.value}{unit_str}"


@dataclass
class PackedDataLine(KvnLine):
    """
    A space-separated data row whose first token is an epoch.

    Used for OEM state vectors and AEM attitude states, where an entire
    record is encoded on a single line with no explicit keys:
    ``EPOCH  x  y  z  x_dot  y_dot  z_dot``

    Attributes
    ----------
    epoch : str
        The epoch string (first token, also available as ``tokens[0]``).
    tokens : list[str]
        All whitespace-separated tokens on the line (epoch + numeric values).
    """

    epoch: str = ""
    tokens: list[str] = field(default_factory=list)

    def to_str(self, **kwargs) -> str:
        return "  ".join(self.tokens)


@dataclass
class CovarianceRowLine(KvnLine):
    """
    A space-separated row of plain numbers inside a covariance block.

    OEM covariance matrix rows contain only numeric tokens with no epoch
    and no key.  Each row represents one row of the lower-triangular matrix:
    ``v11``, ``v21  v22``, ``v31  v32  v33``, …

    Attributes
    ----------
    tokens : list[str]
        The numeric tokens on this row.
    """

    tokens: list[str] = field(default_factory=list)

    def to_str(self, **kwargs) -> str:
        return "  ".join(self.tokens)


def _is_epoch(s: str) -> bool:
    """
    Return ``True`` if ``s`` looks like a CCSDS epoch string.

    A CCSDS epoch starts with a 4-digit year immediately followed by ``"-"``,
    e.g. ``"2007-075T16:50:01"`` or ``"2020-12-29T11:59:56"``.
    """
    return len(s) >= 5 and s[:4].isdigit() and s[4] == "-"


def tokenize(kvn_source: str) -> list[KvnLine]:
    """
    Convert a raw KVN string into an ordered list of :class:`KvnLine` objects.

    Each input line is classified and parsed into the appropriate subclass.
    The rules applied in order are:

    1. Strip surrounding whitespace.  Empty result → :class:`BlankLine`.
    2. Line is in :data:`_SECTION_MARKERS` → :class:`SectionMarkerLine`.
    3. Line starts with ``"COMMENT"`` → :class:`CommentLine`.
       A leading ``"="`` after ``"COMMENT"`` is stripped (handles the
       ``COMMENT = text`` variant).
    4. Line contains ``"="``:\n
       a. Split on the first ``"="`` into *key* and *rest*.
       b. Extract a trailing ``[unit]`` from *rest* if present.
       c. Split remaining *rest* on whitespace.  Two tokens where the first
          looks like an epoch → :class:`TdmObsLine`.  Otherwise → :class:`KvLine`.

    5. No ``"="`` — split on whitespace:

       a. First token looks like an epoch → :class:`PackedDataLine`.
       b. Otherwise → :class:`CovarianceRowLine`.

    Blank lines that appear *before* the first ``CCSDS_`` header line are
    dropped so that files with a leading blank or BOM are handled cleanly.

    Parameters
    ----------
    kvn_source : str
        Raw KVN text (Windows or Unix line endings accepted).

    Returns
    -------
    list[KvnLine]
        Ordered list of classified line objects.
    """
    result: list[KvnLine] = []
    header_seen = False

    for raw_line in kvn_source.splitlines():
        line = raw_line.strip()

        # Drop blank lines before the CCSDS_ header
        if not header_seen:
            if not line:
                continue
            if line.startswith("CCSDS_"):
                header_seen = True

        # --- BlankLine ---
        if not line:
            result.append(BlankLine())
            continue

        # --- SectionMarkerLine ---
        if line in _SECTION_MARKERS:
            result.append(SectionMarkerLine(key=line))
            continue

        # --- CommentLine ---
        if line.startswith("COMMENT"):
            text = line[7:].strip()
            if text.startswith("="):
                text = text[1:].strip()
            result.append(CommentLine(text=text))
            continue

        # --- KvLine or TdmObsLine (line contains "=") ---
        if "=" in line:
            key, rest = line.split("=", maxsplit=1)
            key = key.strip()
            rest = rest.strip()

            # Extract trailing [unit] if present
            unit = ""
            if rest.endswith("]"):
                bracket = rest.rfind("[")
                if bracket >= 0:
                    unit = rest[bracket + 1 : -1].strip()
                    rest = rest[:bracket].strip()

            value_tokens = rest.split()
            if len(value_tokens) == 2 and _is_epoch(value_tokens[0]):
                result.append(
                    TdmObsLine(
                        key=key,
                        epoch=value_tokens[0],
                        value=value_tokens[1],
                        unit=unit,
                    )
                )
            else:
                result.append(KvLine(key=key, value=rest, unit=unit))
            continue

        # --- PackedDataLine or CovarianceRowLine (no "=") ---
        tokens = line.split()
        if tokens and _is_epoch(tokens[0]):
            result.append(PackedDataLine(epoch=tokens[0], tokens=tokens))
        else:
            result.append(CovarianceRowLine(tokens=tokens))

    return result
