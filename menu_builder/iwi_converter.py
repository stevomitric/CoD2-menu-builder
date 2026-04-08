"""Convert images to CoD2 IWI format via DDS (BC3/DXT5).

Pipeline: PNG/JPG -> DDS (BC3 via quicktex) -> IWI (CoD2 format)

Requires: pip install quicktex
"""

from __future__ import annotations

import struct
import subprocess
import tempfile
from pathlib import Path


def png_to_dds(input_path: Path, output_path: Path) -> Path:
    """Convert a PNG/JPG to DDS BC3 format using quicktex CLI.

    Args:
        input_path: Path to the source image (PNG or JPG).
        output_path: Path for the output .dds file.

    Returns:
        Path to the written DDS file.
    """
    result = subprocess.run(
        ["quicktex", "encode", "bc3", "--no-flip", str(input_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"quicktex failed: {result.stderr.strip()}")

    # quicktex writes output next to input with .dds extension
    generated = input_path.with_suffix(".dds")
    if generated != output_path:
        generated.rename(output_path)

    return output_path


def dds_bc3_to_iwi(dds_path: Path, iwi_output: Path) -> Path:
    """Convert a DDS BC3 file to CoD2 IWI format (no mipmaps).

    Args:
        dds_path: Path to the DDS (BC3/DXT5) file.
        iwi_output: Path for the output .iwi file.

    Returns:
        Path to the written IWI file.
    """
    dds_data = dds_path.read_bytes()

    # Parse DDS header
    height = struct.unpack("<I", dds_data[12:16])[0]
    width = struct.unpack("<I", dds_data[16:20])[0]
    pixel_data = dds_data[128:]  # skip 128-byte DDS header

    total_iwi_size = 28 + len(pixel_data)

    # CoD2 IWI header (28 bytes):
    #   3B  Tag 'IWi'
    #   1B  Version 5 (CoD2)
    #   1B  Format 0x0D (BC3/DXT5)
    #   1B  Flags 0
    #   2B  Width
    #   2B  Height
    #   2B  Z-Depth (1)
    #   4B  Total file size
    #   4B  Mip0 offset (28 = right after header)
    #   4B  Mip1 offset (0 = no mips)
    #   4B  Mip2 offset (0 = no mips)
    header = struct.pack("<3sBBBHH", b"IWi", 5, 0x0D, 0, width, height)
    header += struct.pack("<H", 1)                # z-depth
    header += struct.pack("<I", total_iwi_size)   # total size
    header += struct.pack("<I", 28)               # mip0 offset
    header += struct.pack("<I", 0)                # mip1 (none)
    header += struct.pack("<I", 0)                # mip2 (none)

    iwi_output.parent.mkdir(parents=True, exist_ok=True)
    with open(iwi_output, "wb") as f:
        f.write(header)
        f.write(pixel_data)

    return iwi_output


def image_to_iwi(input_path: Path, iwi_output: Path) -> Path:
    """Convert a PNG/JPG image to CoD2 IWI format.

    Full pipeline: image -> DDS (BC3) -> IWI.

    Args:
        input_path: Path to the source image.
        iwi_output: Path for the output .iwi file.

    Returns:
        Path to the written IWI file.
    """
    with tempfile.TemporaryDirectory() as tmp:
        dds_path = Path(tmp) / input_path.with_suffix(".dds").name
        png_to_dds(input_path, dds_path)
        return dds_bc3_to_iwi(dds_path, iwi_output)
