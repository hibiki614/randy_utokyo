from pathlib import Path
import ctypes
import numpy as np
lib=ctypes.CDLL(str(Path(__file__).resolve().parent/'queue_fast.so'))
ptr=np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags='C_CONTIGUOUS')
lib.corridor_delay.argtypes=[ctypes.c_int,ptr,ctypes.c_double,ptr,ptr,ctypes.c_int]
lib.corridor_delay.restype=ctypes.c_double

def delay(L,v,x,g,warm=12):
 a,b,c=[np.ascontiguousarray(t,dtype=np.float64) for t in [L,x,g]]
 d=lib.corridor_delay(len(g),a,float(v),b,c,warm)
 if not np.isfinite(d):raise ValueError('Invalid delay: unserved cohort')
 return d
