import struct
from PIL import Image
import io, os
import quicktex
from quicktex.s3tc.bc3 import BC3Encoder


def dds_bc1_to_iwi_menu(dds_path, iwi_output):
    with open(dds_path, "rb") as f:
        dds_data = f.read()

    # 1. Parse DDS Header
    # Height at 12, Width at 16, FourCC at 84
    height = struct.unpack('<I', dds_data[12:16])[0]
    width = struct.unpack('<I', dds_data[16:20])[0]
    dds_data = dds_data[128:]

    # 2. Calculate Sizes for BC3 (1 byte per pixel)
    # Since this is a menu (No Mips), we only take the first width * height bytes
    total_iwi_size = 28 + len(dds_data)

    print(f"Decoded DDS:")
    print(f" - Width: {width}")
    print(f" - Height: {height}")
    print(f" - IWi size: {total_iwi_size}")
    

    # 3. Create the 28-Byte CoD2 Header
    # - 3B Tag 'IWi'
    # - 1B Ver 5 (COD2),
    # - 1B Format (UNKNOWN),
    # - 1B Flags 0,
    # - 2B Width,
    # - 2B Height
    header = struct.pack('<3sBBBHH', b'IWi', 5, 0x0B, 0, width, height)
    
    # Offset 10: Z-Depth
    header += struct.pack('<H', 1) 
    # Offset 12: The Checksum (Total File Size)
    header += struct.pack('<I', total_iwi_size)
    
    # Offset 16: Mipmap Offsets/Sizes
    # Since we have no mips, we set Mip0 to the full size and others to 0
    header += struct.pack('<I', 28) 
    header += struct.pack('<I', 0) 
    header += struct.pack('<I', 0) 

    print(' '.join([header.hex()[i: i+2] for i in range(0, len(header.hex()), 2)]))

    # 5. Write the File
    with open(iwi_output, "wb") as f:
        f.write(header)
        f.write(dds_data)

    print(f"Successfully converted {dds_path} to {iwi_output}")
    print(f"IWI Format: DXT5 (0x04) | Mips: No")
    print(f"Final Size: {os.path.getsize(iwi_output)} bytes")


def dds_bc3_to_iwi_menu(dds_path, iwi_output):
    with open(dds_path, "rb") as f:
        dds_data = f.read()

    # 1. Parse DDS Header
    # Height at 12, Width at 16, FourCC at 84
    height = struct.unpack('<I', dds_data[12:16])[0]
    width = struct.unpack('<I', dds_data[16:20])[0]
    dds_data = dds_data[128:]

    # 2. Calculate Sizes for BC3 (1 byte per pixel)
    # Since this is a menu (No Mips), we only take the first width * height bytes
    total_iwi_size = 28 + len(dds_data)

    print(f"Decoded DDS:")
    print(f" - Width: {width}")
    print(f" - Height: {height}")
    print(f" - IWi size: {total_iwi_size}")
    

    # 3. Create the 28-Byte CoD2 Header
    # - 3B Tag 'IWi'
    # - 1B Ver 5 (COD2),
    # - 1B Format (UNKNOWN),
    # - 1B Flags 0,
    # - 2B Width,
    # - 2B Height
    header = struct.pack('<3sBBBHH', b'IWi', 5, 0x0D, 0, width, height)
    
    # Offset 10: Z-Depth
    header += struct.pack('<H', 1) 
    # Offset 12: The Checksum (Total File Size)
    header += struct.pack('<I', total_iwi_size)
    
    # Offset 16: Mipmap Offsets/Sizes
    # Since we have no mips, we set Mip0 to the full size and others to 0
    header += struct.pack('<I', 28) 
    header += struct.pack('<I', 0) 
    header += struct.pack('<I', 0) 

    print(' '.join([header.hex()[i: i+2] for i in range(0, len(header.hex()), 2)]))

    # 5. Write the File
    with open(iwi_output, "wb") as f:
        f.write(header)
        f.write(dds_data)

    print(f"Successfully converted {dds_path} to {iwi_output}")
    print(f"IWI Format: DXT5 (0x04) | Mips: No")
    print(f"Final Size: {os.path.getsize(iwi_output)} bytes")


# Example usage
# iwi_to_png("egypt_window1.iwi", "out.png")
#png_to_iwi_16bit_02("out.dds", "out.iwi")
dds_bc3_to_iwi_menu("egypt_window1.dds", "out.iwi")