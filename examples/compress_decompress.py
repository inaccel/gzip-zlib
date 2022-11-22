import inaccel.coral as inaccel
import numpy as np

from inaccel.gzip import compress
from gzip import decompress

with inaccel.allocator:
    data = np.random.randn(1000000).astype(np.ubyte).data

assert decompress(compress(data)) == data
