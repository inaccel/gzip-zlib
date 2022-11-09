import numpy as np

from inaccel.gzip import compress
from gzip import decompress

data = np.random.bytes(1024)

assert decompress(compress(data)) == data
