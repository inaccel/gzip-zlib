import inaccel.coral as inaccel
import numpy as np
import struct
import zlib

KVEC = 16
KMINBUFFERSIZE = 16384
MINIMUM_FILESIZE = KVEC + 1


def crc_compute(data, size, previous_crc):
    num_nibbles_parallel = 64
    num_sections = int(size // (num_nibbles_parallel / 2))
    remaining_bytes = int(size % (num_nibbles_parallel / 2))

    if (remaining_bytes == 0):
        return previous_crc

    idx = int(num_sections * (num_nibbles_parallel / 2))
    return previous_crc if (idx == size) else zlib.crc32(
        data[idx:], previous_crc)


def calcMaxTempSize(data_size):
    tmp_size = data_size + 16 * KVEC
    tmp_size = KMINBUFFERSIZE if tmp_size < KMINBUFFERSIZE else tmp_size
    return tmp_size


def compress(data, *, level=zlib.Z_BEST_SPEED, wbits=zlib.MAX_WBITS):
    if (level != zlib.Z_BEST_SPEED) or ((wbits > -9) and (wbits < 25)):
        raise zlib.error('Bad compression level')

    data_size = np.int64(len(data))
    if (data_size < MINIMUM_FILESIZE):
        raise zlib.error('FPGA minimum supported file size: ' +
                         str(MINIMUM_FILESIZE) + ', given: ' + str(data_size))

    compressed_data_size = np.int64(calcMaxTempSize(data_size))
    gzip_info_size = np.int64(16)
    crc_size = np.int64(4)
    last_block = np.int32(1)
    nil = np.int64(0)

    with inaccel.allocator:
        compressed_data = np.ndarray(compressed_data_size + 64 + 8,
                                     dtype=np.ubyte)
        gzip_info = np.ndarray(2, dtype=np.uint)
        crc = np.ndarray(1, dtype=np.uint32)

    req = inaccel.request('intel.compression.gzip')

    req.arg(data_size) \
        .arg_array(np.frombuffer(data, dtype=np.ubyte)) \
        .arg(data_size) \
        .arg(nil) \
        .arg(compressed_data[64:]) \
        .arg(compressed_data_size) \
        .arg(nil) \
        .arg(gzip_info) \
        .arg(gzip_info_size) \
        .arg(nil) \
        .arg(crc) \
        .arg(crc_size) \
        .arg(nil) \
        .arg(last_block)

    inaccel.submit(req).result()

    if (wbits >= -15) and (wbits <= -9):
        return compressed_data[64:64 + int(gzip_info[0])].data
    elif (wbits >= 25) and (wbits <= 31):
        struct.pack_into('<BBBBLBB', compressed_data, 54, 0x1f, 0x8b, 8, 0, 0,
                         4, 3)
        struct.pack_into('<LL', compressed_data, 64 + int(gzip_info[0]),
                         crc_compute(data, data_size, crc[0]),
                         (len(data) & 0xffffffff))

        return compressed_data[54:64 + int(gzip_info[0]) + 8].data
