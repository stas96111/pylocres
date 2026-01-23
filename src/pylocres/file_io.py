from io import SEEK_CUR, SEEK_END, SEEK_SET, BytesIO
import mmap
import os
import struct
from uuid import UUID
from typing import List, Optional
from pathlib import Path

_STRUCTS = {
    "<": {
        "u8": struct.Struct("<B"),
        "u16": struct.Struct("<H"),
        "u32": struct.Struct("<I"),
        "u64": struct.Struct("<Q"),
        "i8": struct.Struct("<b"),
        "i16": struct.Struct("<h"),
        "i32": struct.Struct("<i"),
        "i64": struct.Struct("<q"),
    },
    ">": {
        "u8": struct.Struct(">B"),
        "u16": struct.Struct(">H"),
        "u32": struct.Struct(">I"),
        "u64": struct.Struct(">Q"),
        "i8": struct.Struct(">b"),
        "i16": struct.Struct(">h"),
        "i32": struct.Struct(">i"),
        "i64": struct.Struct(">q"),
    },
}


class Endian:
    BIG = ">"
    LITTLE = "<"


class Reader:
    __slots__ = (
        "path",
        "size",
        "pos",
        "endian",
        "_mm",
        "_view",
        "_file_obj",
        "_u8",
        "_u16",
        "_u32",
        "_u64",
        "_i8",
        "_i16",
        "_i32",
        "_i64",
    )

    def __init__(self, file: Path | str | bytes = b"", endian: str = "<"):
        self.path = None
        self.size = 0
        self.pos = 0
        self.set_endian(endian)

        self._mm = None
        self._view = None
        self._file_obj = None

        if isinstance(file, str):
            self.path = str(Path(file))
            self._file_obj = open(file, "rb")
            self._mm = mmap.mmap(self._file_obj.fileno(), 0, access=mmap.ACCESS_READ)
            self._view = memoryview(self._mm)
            self.size = len(self._mm)
        elif isinstance(file, (bytes, bytearray)):
            self._mm = None  # IMPORTANT
            self._view = memoryview(file)
            self.size = len(file)
        else:
            raise ValueError("File must be: str(path), bytes, or bytearray.")

    def set_endian(self, endian: str = ">"):
        self.endian = endian
        s = _STRUCTS[endian]
        self._u8 = s["u8"]
        self._u16 = s["u16"]
        self._u32 = s["u32"]
        self._u64 = s["u64"]
        self._i8 = s["i8"]
        self._i16 = s["i16"]
        self._i32 = s["i32"]
        self._i64 = s["i64"]

    def close(self):
        if self._view is not None:
            self._view.release()
            self._view = None

        if self._mm is not None:
            self._mm.close()
            self._mm = None

        if self._file_obj is not None:
            self._file_obj.close()
            self._file_obj = None

    def reopen(self):
        """Reopen the file if it was closed."""
        if self.path and self._file_obj is None:
            self._file_obj = open(self.path, "rb")
            self._mm = mmap.mmap(self._file_obj.fileno(), 0, access=mmap.ACCESS_READ)
            self._view = memoryview(self._mm)
            self.size = len(self._mm)
            self.pos = 0

    def get_pos(self):
        return self.pos

    def set_pos(self, position: int, where=SEEK_SET):
        if where == SEEK_CUR:
            self.pos += position
        elif where == SEEK_END:
            self.pos = self.size - abs(position)
        elif where == SEEK_SET:
            self.pos = position

    def move(self, offset: int):
        self.set_pos(offset, SEEK_CUR)

    def get_size(self):
        return self.size

    def read(self, size: int) -> bytes:
        """Read bytes directly from memory-mapped file without bounds checking in hot path."""
        pos = self.pos
        end = pos + size
        if end > self.size:
            raise EOFError(f"Attempt to read {size} beyond the end of the file.")
        data = self._view[pos:end]
        self.pos = end
        return data.tobytes()

    def read_int(self, size: int, signed: bool = False, byteorder="little") -> int:
        val = self._view[self.pos : self.pos + size]
        self.pos += size
        return int.from_bytes(val, byteorder=byteorder, signed=signed)

    def read_into(self, size: int, buffer) -> int:
        """Read directly into a pre-allocated buffer for zero-copy efficiency."""
        pos = self.pos
        end = pos + size
        if end > self.size:
            raise EOFError(f"Attempt to read {size} beyond the end of the file.")
        buffer[:] = self._view[pos:end]
        self.pos = end
        return size

    def uint(self) -> int:
        val = self._u8.unpack_from(self._view, self.pos)[0]
        self.pos += 1
        return val

    def uint8(self) -> int:
        val = self._u8.unpack_from(self._view, self.pos)[0]
        self.pos += 1
        return val

    def uint16(self) -> int:
        val = self._u16.unpack_from(self._view, self.pos)[0]
        self.pos += 2
        return val

    def uint32(self) -> int:
        val = self._u32.unpack_from(self._view, self.pos)[0]
        self.pos += 4
        return val

    def uint64(self) -> int:
        val = self._u64.unpack_from(self._view, self.pos)[0]
        self.pos += 8
        return val

    def int(self) -> int:
        val = self._i8.unpack_from(self._view, self.pos)[0]
        self.pos += 1
        return val

    def int8(self) -> int:
        val = self._i8.unpack_from(self._view, self.pos)[0]
        self.pos += 1
        return val

    def int16(self) -> int:
        val = self._i16.unpack_from(self._view, self.pos)[0]
        self.pos += 2
        return val

    def int32(self) -> int:
        val = self._i32.unpack_from(self._view, self.pos)[0]
        self.pos += 4
        return val

    def int64(self) -> int:
        val = self._i64.unpack_from(self._view, self.pos)[0]
        self.pos += 8
        return val

    def bool(self) -> bool:
        val = self.uint8()
        return val != 0

    def sha1(self) -> bytes:
        return self.read(20)

    def guid(self) -> UUID:
        data = self.read(16)
        return UUID(bytes_le=data)

    def string(self, length=None):
        if length is None:
            length = self.int32()

        if length > 0:
            s = self._view[self.pos : self.pos + length]
            self.pos += length
            return bytes(s).decode("ascii", errors="replace").rstrip("\0")
        elif length < 0:
            # string = self.read(length * -2).decode("utf-16le", errors="replace")
            size = length * -2
            s = self._view[self.pos : self.pos + size]
            self.pos += size
            return bytes(s).decode("utf-16le", errors="replace").rstrip("\0")
        else:
            return ""
        return string.rstrip("\0")

    def list(self, func, length=None):
        if length is None:
            length = self.uint32()
        return [func(self) for _ in range(length)]

    def strings_list(self, length=None):
        return self.list(self.string, length=length)

    def buffer(self, offset, size):
        data = self._view[offset : offset + size].tobytes()
        return Reader(data)

    def reopen(self):
        self.close()
        if self.path is None:
            self.__init__(endian=self.endian)
        elif self._mm is None:
            self.__init__(self.path, endian=self.endian)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class Writer:
    __slots__ = (
        "path",
        "size",
        "pos",
        "endian",
        "_mm",
        "_view",
        "_file_obj",
        "_buf",
        "_u8",
        "_u16",
        "_u32",
        "_u64",
        "_i8",
        "_i16",
        "_i32",
        "_i64",
    )

    def __init__(
        self, file: str | int | None = None, endian: str = "<", initial_size=1024
    ):
        """
        file:
          - str  -> file path (mmap-backed)
          - None -> in-memory (bytearray)
        """
        self.path = None
        self.pos = 0
        self.size = 0
        self._mm = None
        self._view = None
        self._file_obj = None
        self._buf = None

        self.set_endian(endian)

        if isinstance(file, str):
            self.path = file
            self._file_obj = open(file, "w+b")
            self._file_obj.truncate(initial_size)
            self._mm = mmap.mmap(self._file_obj.fileno(), initial_size)
            self._view = memoryview(self._mm)
            self.size = initial_size

        elif file is None:
            self._buf = bytearray(initial_size)
            self._view = memoryview(self._buf)
            self.size = initial_size

        else:
            raise ValueError("Writer file must be: str(path) or None")

    # ------------------ internal ------------------

    def _ensure(self, needed: int):
        if self.pos + needed <= self.size:
            return

        new_size = max(self.size * 2, self.pos + needed)

        if self._mm is not None:
            if self._view is not None:
                self._view.release()
                self._view = None

            self._mm.resize(new_size)

            self._view = memoryview(self._mm)
        else:
            self._buf.extend(b"\x00" * (new_size - self.size))
            self._view = memoryview(self._buf)

        self.size = new_size

    # ------------------ endian ------------------

    def set_endian(self, endian: str):
        self.endian = endian
        s = _STRUCTS[endian]
        self._u8 = s["u8"]
        self._u16 = s["u16"]
        self._u32 = s["u32"]
        self._u64 = s["u64"]
        self._i8 = s["i8"]
        self._i16 = s["i16"]
        self._i32 = s["i32"]
        self._i64 = s["i64"]

    # ------------------ position ------------------

    def get_pos(self):
        return self.pos

    def set_pos(self, position: int, where=SEEK_SET):
        if where == SEEK_SET:
            self.pos = position
        elif where == SEEK_CUR:
            self.pos += position
        elif where == SEEK_END:
            self.pos = self.size - position
        else:
            raise ValueError("Invalid seek mode")

    def move(self, offset: int):
        self.pos += offset

    # ------------------ raw write ------------------

    def write(self, data: bytes | bytearray | memoryview):
        n = len(data)
        self._ensure(n)
        self._view[self.pos : self.pos + n] = data
        self.pos += n

    # ------------------ typed writes ------------------

    def uint8(self, v: int):
        self._ensure(1)
        self._u8.pack_into(self._view, self.pos, v)
        self.pos += 1

    def uint16(self, v: int):
        self._ensure(2)
        self._u16.pack_into(self._view, self.pos, v)
        self.pos += 2

    def uint32(self, v: int):
        self._ensure(4)
        self._u32.pack_into(self._view, self.pos, v)
        self.pos += 4

    def uint64(self, v: int):
        self._ensure(8)
        self._u64.pack_into(self._view, self.pos, v)
        self.pos += 8

    def uint128(self, v: int):
        self._ensure(16)
        self._view[self.pos : self.pos + 16] = v.to_bytes(
            16, "little" if self.endian == "<" else "big", signed=False
        )
        self.pos += 16

    def int8(self, v: int):
        self._ensure(1)
        self._i8.pack_into(self._view, self.pos, v)
        self.pos += 1

    def int16(self, v: int):
        self._ensure(2)
        self._i16.pack_into(self._view, self.pos, v)
        self.pos += 2

    def int32(self, v: int):
        self._ensure(4)
        self._i32.pack_into(self._view, self.pos, v)
        self.pos += 4

    def int64(self, v: int):
        self._ensure(8)
        self._i64.pack_into(self._view, self.pos, v)
        self.pos += 8

    def int128(self, v: int):
        self._ensure(16)
        self._view[self.pos : self.pos + 16] = v.to_bytes(
            16, "little" if self.endian == "<" else "big", signed=True
        )
        self.pos += 16

    def bool(self, v: bool):
        self.uint8(1 if v else 0)

    # ------------------ output ------------------

    def getvalue(self) -> bytes:
        if self._buf is None:
            raise RuntimeError("Writer is file-backed")
        return bytes(self._buf[: self.pos])

    def close(self):
        # Release memoryview FIRST
        if self._view is not None:
            try:
                self._view.release()
            except AttributeError:
                pass
            self._view = None

        # Shrink file-backed storage to actual data size
        if self._mm is not None:
            self._mm.flush()
            self._mm.close()
            self._mm = None

            # IMPORTANT: truncate AFTER closing mmap
            self._file_obj.truncate(self.pos)

        # Then close file
        if self._file_obj is not None:
            self._file_obj.close()
            self._file_obj = None

    def sha1(self, data: bytes):
        if len(data) != 20:
            raise ValueError("SHA1 must be 20 bytes")
        self.write(data)

    def guid(self, value: UUID):
        self.write(value.bytes_le)

    def string(self, value: str, use_unicode: bool = False):
        value += "\x00"
        if (not use_unicode) and value.isascii():
            self.uint32(len(value))
            self.write(value.encode("ascii"))
        else:
            encoded = value.encode("utf-16le")
            self.int32(-(len(encoded) // 2))
            self.write(encoded)

    def list(self, list_items: List[bytes], write_length: bool = False):
        if write_length:
            self.uint32(len(list_items))
        for item in list_items:
            self.write(item)

    def strings_list(self, list_items: List[str], write_length: bool = False):
        if write_length:
            self.uint32(len(list_items))
        for item in list_items:
            self.string(item)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
