"""Exact BDF dense polynomials backed by a private, rebuildable disk cache.

This changes storage only: each accepted BDF polynomial is written as float64
bytes, then evaluated with SciPy's original BdfDenseOutput implementation.
No additional time/space interpolation and no solver restart are introduced.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import tempfile
import numpy as np
from scipy.integrate._ivp.bdf import BDF, BdfDenseOutput
from scipy.integrate._ivp.base import DenseOutput

LOADED_CODE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class DenseCache:
    def __init__(self, root):
        self.parent = (Path(root)/'tmp/cache/solver_runs').resolve()
        self.parent.mkdir(parents=True, exist_ok=True)
        self.directory = Path(tempfile.mkdtemp(prefix='bdf_', dir=self.parent)).resolve()
        self.handle = (self.directory/'polynomials.bin').open('w+b', buffering=0)
        self.bytes_written = 0
        self.polynomial_count = 0
        self.accepted_arrays = []
        self.closed = False

    def append(self, values):
        if self.closed:
            raise RuntimeError('Dense solution cache is closed')
        array = np.ascontiguousarray(values, dtype=np.float64)
        offset = self.bytes_written
        self.handle.seek(offset)
        array.tofile(self.handle)
        self.bytes_written += array.nbytes
        self.polynomial_count += 1
        return offset, array.shape

    def read(self, offset, shape):
        if self.closed:
            raise RuntimeError('Dense solution cache is closed')
        count = int(np.prod(shape))
        self.handle.seek(offset)
        values = np.fromfile(self.handle, dtype=np.float64, count=count)
        if values.size != count:
            raise IOError('Incomplete BDF coefficient cache')
        return values.reshape(shape)

    def store_accepted(self, values):
        path = self.directory/f'accepted_{len(self.accepted_arrays):03d}.npy'
        mapped = np.lib.format.open_memmap(path, mode='w+', dtype=values.dtype, shape=values.shape)
        mapped[:] = values
        mapped.flush()
        self.accepted_arrays.append(mapped)
        return mapped

    def close(self):
        if self.closed:
            return
        self.handle.close()
        for array in self.accepted_arrays:
            array._mmap.close()
        self.accepted_arrays.clear()
        # Delete only the verified private cache created by this object.
        if self.directory.parent != self.parent or not self.directory.name.startswith('bdf_'):
            raise RuntimeError('Unexpected private cache path; cleanup refused')
        for path in self.directory.iterdir():
            if not path.is_file() or path.is_symlink():
                raise RuntimeError('Unexpected cache entry; cleanup refused')
            path.unlink()
        self.directory.rmdir()
        self.closed = True


class FileBdfDenseOutput(DenseOutput):
    def __init__(self, original, cache):
        super().__init__(original.t_old, original.t)
        self.order = original.order
        self.t_shift = original.t_shift.copy()
        self.denom = original.denom.copy()
        self.cache = cache
        self.offset, self.shape = cache.append(original.D)

    def _call_impl(self, t):
        # Reuse the installed SciPy evaluator with the exact recorded D bytes.
        dense = object.__new__(BdfDenseOutput)
        dense.D = self.cache.read(self.offset, self.shape)
        dense.t_shift, dense.denom = self.t_shift, self.denom
        return dense._call_impl(t)


class DiskBDF(BDF):
    def __init__(self, *args, dense_cache, **kwargs):
        self.dense_cache = dense_cache
        super().__init__(*args, **kwargs)

    def _dense_output_impl(self):
        return FileBdfDenseOutput(super()._dense_output_impl(), self.dense_cache)
