import gzip
import inaccel.zlib
import struct
import time
import zlib


def _create_simple_gzip_header(compresslevel: int,
                               mtime = None) -> bytes:
    """
    Write a simple gzip header with no extra fields.
    :param compresslevel: Compresslevel used to determine the xfl bytes.
    :param mtime: The mtime (must support conversion to a 32-bit integer).
    :return: A bytes object representing the gzip header.
    """
    if mtime is None:
        mtime = time.time()
    if compresslevel == gzip._COMPRESS_LEVEL_BEST:
        xfl = 2
    elif compresslevel == gzip._COMPRESS_LEVEL_FAST:
        xfl = 4
    else:
        xfl = 0
    # Pack ID1 and ID2 magic bytes, method (8=deflate), header flags (no extra
    # fields added to header), mtime, xfl and os (255 for unknown OS).
    return struct.pack("<BBBBLBB", 0x1f, 0x8b, 8, 0, int(mtime), xfl, 255)


def compress(data, compresslevel=gzip._COMPRESS_LEVEL_BEST, *, mtime=None):
    """Compress data in one shot and return the compressed string.
    compresslevel sets the compression level in range of 0-9.
    mtime can be used to set the modification time. The modification time is
    set to the current time by default.
    """
    if mtime == 0:
        # Use zlib as it creates the header with 0 mtime by default.
        # This is faster and with less overhead.
        return inaccel.zlib.compress(data, level=compresslevel, wbits=31)
    header = _create_simple_gzip_header(compresslevel, mtime)
    trailer = struct.pack("<LL", zlib.crc32(data), (len(data) & 0xffffffff))
    # Wbits=-15 creates a raw deflate block.
    return (header + inaccel.zlib.compress(data, level=compresslevel, wbits=-15) +
            trailer)
