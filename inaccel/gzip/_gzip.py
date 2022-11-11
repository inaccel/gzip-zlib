import gzip
import inaccel.zlib
import struct
import time


def compress(data, compresslevel=gzip._COMPRESS_LEVEL_FAST, *, mtime=None):
    """Compress data in one shot and return the compressed string.
    compresslevel sets the compression level in range of 0-9.
    mtime can be used to set the modification time. The modification time is
    set to the current time by default.
    """
    if mtime is None:
        mtime = time.time()
    # Use inaccel.zlib as it creates the header with 0 mtime by default.
    # This is faster and with less overhead.
    compressed_data = inaccel.zlib.compress(data, level=compresslevel, wbits=31)
    if mtime != 0:
        struct.pack_into("<L", compressed_data, 4, int(mtime))
    return compressed_data
