import struct
from functools import singledispatch
from typing import List, Tuple, Union

# Constants
K0 = 0xc3a5c85c97cb3127
K1 = 0xb492b66fbe98f273
K2 = 0x9ae16a3b2f90404f
K3 = 0xc949d7c7509e6557
C1 = 0xcc9e2d51
C2 = 0x1b873593
HASH_MUL = 0x9ddfea08eb382d69  # 11376068507788127593 in original
BIG_ENDIAN = False  # Set to True if running on big-endian system

class CityHash:
    @staticmethod
    def _uint64(x: int) -> int:
        """Ensure value is a 64-bit unsigned integer."""
        return x & 0xFFFFFFFFFFFFFFFF
    
    @staticmethod
    def _uint32(x: int) -> int:
        """Ensure value is a 32-bit unsigned integer."""
        return x & 0xFFFFFFFF
    
    @staticmethod
    def byte_swap_uint32(x: int) -> int:
        """Swap byte order for a 32-bit integer."""
        x = CityHash._uint32(x)
        return (
            (x >> 24) |
            ((x & 0x00ff0000) >> 8) |
            ((x & 0x0000ff00) << 8) |
            (x << 24)
        )
    
    @staticmethod
    def byte_swap_uint64(x: int) -> int:
        """Swap byte order for a 64-bit integer."""
        x = CityHash._uint64(x)
        return (
            (x >> 56) |
            ((x & 0x00ff000000000000) >> 40) |
            ((x & 0x0000ff0000000000) >> 24) |
            ((x & 0x000000ff00000000) >> 8) |
            ((x & 0x00000000ff000000) << 8) |
            ((x & 0x0000000000ff0000) << 24) |
            ((x & 0x000000000000ff00) << 40) |
            (x << 56)
        )
    
    @staticmethod
    def hash128_to_64(x: List[int]) -> int:
        """Hash a pair of 64-bit integers into a 64-bit integer."""
        a = CityHash._uint64((x[0] ^ x[1]) * HASH_MUL)
        a ^= (a >> 47)
        b = CityHash._uint64((x[1] ^ a) * HASH_MUL)
        b ^= (b >> 47)
        b = CityHash._uint64(b * HASH_MUL)
        return b
    
    @staticmethod
    def fetch32(data: bytes, index: int) -> int:
        """Fetch a 32-bit integer from data at the given index."""
        x = struct.unpack_from('<I', data, index)[0]
        return CityHash._uint64(CityHash.byte_swap_uint32(x) if BIG_ENDIAN else x)
    
    @staticmethod
    def fetch64(data: bytes, index: int) -> int:
        """Fetch a 64-bit integer from data at the given index."""
        x = struct.unpack_from('<Q', data, index)[0]
        return CityHash._uint64(CityHash.byte_swap_uint64(x) if BIG_ENDIAN else x)
    
    @staticmethod
    def rotate(val: int, shift: int) -> int:
        """Rotate a 64-bit integer by shift bits."""
        val = CityHash._uint64(val)
        if shift == 0:
            return CityHash._uint64(val)
        return CityHash._uint64((val >> shift) | (val << (64 - shift)))
    
    @staticmethod
    def shift_mix(val: int) -> int:
        """Mix a 64-bit integer by shifting."""
        
        val = CityHash._uint64(val)
        return CityHash._uint64(val ^ (val >> 47))
    
    @staticmethod
    @singledispatch
    def hash_len16(u: int, v: int, mul: int = None) -> int:
        """Hash two 64-bit integers into a 64-bit integer."""
        if mul is None:
            return CityHash.hash128_to_64([u, v])
        
        u, v = CityHash._uint64(u), CityHash._uint64(v)
        mul = CityHash._uint64(mul)
        
        a = CityHash._uint64((u ^ v) * mul)
        a ^= (a >> 47)
        b = CityHash._uint64((v ^ a) * mul)
        b ^= (b >> 47)
        b = CityHash._uint64(b * mul)
        return b
    
    @staticmethod
    def hash_len0_to_16(data: bytes, offset: int) -> int:
        """Hash strings of length 0 to 16."""
        length = len(data) - offset
        
        if length >= 8:
            mul = K2 + length * 2
            a = CityHash.fetch64(data, offset) + K2
            b = CityHash.fetch64(data, offset + length - 8)
            c = CityHash._uint64(CityHash.rotate(b, 37) * mul + a)
            d = CityHash._uint64((CityHash.rotate(a, 25) + b) * mul)
            return CityHash.hash_len16(c, d, mul)
        
        if length >= 4:
            mul = K2 + length * 2
            a = CityHash.fetch32(data, offset)
            return CityHash.hash_len16(length + (a << 3), 
                                      CityHash.fetch32(data, offset + length - 4), 
                                      mul)
        
        if length > 0:
            a = data[offset]
            b = data[offset + (length >> 1)]
            c = data[offset + (length - 1)]
            y = a + (b << 8)
            z = length + (c << 2)
            return CityHash._uint64(CityHash.shift_mix((y * K2) ^ (z * K0)) * K2)
        
        return K2
    
    @staticmethod
    def hash_len17_to_32(data: bytes) -> int:
        """Hash strings of length 17 to 32."""
        length = len(data)
        mul = CityHash._uint64(K2 + length * 2)
        
        a = CityHash._uint64(CityHash.fetch64(data, 0) * K1)
        b = CityHash.fetch64(data, 8)
        c = CityHash._uint64(CityHash.fetch64(data, length - 8) * mul)
        d = CityHash._uint64(CityHash.fetch64(data, length - 16) * K2)
        
        return CityHash.hash_len16(
            CityHash._uint64(CityHash.rotate(a + b, 43) + CityHash.rotate(c, 30) + d),
            CityHash._uint64(a + CityHash.rotate(b + K2, 18) + c),
            mul
        )
    
    @staticmethod
    def hash_len33_to_64(data: bytes) -> int:
        """Hash strings of length 33 to 64."""
        length = len(data)
        mul = CityHash._uint64(K2 + length * 2)
        
        a = CityHash._uint64(CityHash.fetch64(data, 0) * K2)
        b = CityHash.fetch64(data, 8)
        c = CityHash.fetch64(data, length - 24)
        d = CityHash.fetch64(data, length - 32)
        e = CityHash._uint64(CityHash.fetch64(data, 16) * K2)
        f = CityHash._uint64(CityHash.fetch64(data, 24) * 9)
        g = CityHash.fetch64(data, length - 8)
        h = CityHash._uint64(CityHash.fetch64(data, length - 16) * mul)
        
        u = CityHash._uint64(CityHash.rotate(a + g, 43) + (CityHash.rotate(b, 30) + c) * 9)
        v = CityHash._uint64((a + g) ^ d) + f + 1
        w = CityHash._uint64(CityHash.byte_swap_uint64((u + v) * mul) + h)  # Note ByteSwap here
        x = CityHash._uint64(CityHash.rotate(e + f, 42) + c)
        y = CityHash._uint64(CityHash.byte_swap_uint64((v + w) * mul) + g) * mul  # Note ByteSwap here
        z = CityHash._uint64(e + f + c)
        
        a = CityHash._uint64(CityHash.byte_swap_uint64((x + z) * mul + y) + b)  # Note ByteSwap here
        b = CityHash._uint64(CityHash.shift_mix((z + a) * mul + d + h) * mul)
        
        return CityHash._uint64(b + x)
    
    @staticmethod
    def weak_hash_len32_with_seeds(w: int, x: int, y: int, z: int, a: int, b: int) -> List[int]:
        """Compute a weak hash with seeds for a 32-byte chunk."""
        a += w
        b = CityHash.rotate(b + a + z, 21)
        c = a
        a += x
        a += y
        b += CityHash.rotate(a, 44)
        
        return [CityHash._uint64(a + z), CityHash._uint64(b + c)]
    
    @staticmethod
    def weak_hash_len32_with_seeds_from_bytes(data: bytes, offset: int, a: int, b: int) -> List[int]:
        """Compute a weak hash with seeds from a 32-byte chunk in data."""
        return CityHash.weak_hash_len32_with_seeds(
            CityHash.fetch64(data, offset),
            CityHash.fetch64(data, offset + 8),
            CityHash.fetch64(data, offset + 16),
            CityHash.fetch64(data, offset + 24),
            a, b
        )
    
    @staticmethod
    def city_hash_64_utf16_to_uint32(s: str) -> int:
        """Compute a 32-bit hash from a UTF-16 string."""
        if not s:
            return 0
        
        h = CityHash.city_hash_64(s)
        r = CityHash._uint32((h & 0xFFFFFFFF) + (((h >> 32) & 0xFFFFFFFF) * 23))
        return r
    
    @staticmethod
    def city_hash_64(s: str) -> int:
        """Compute a 64-bit hash from a string."""
        data = s.encode('utf-16le')
        length = len(data)
        
        # Handle short strings
        if length <= 32:
            if length <= 16:
                return CityHash.hash_len0_to_16(data, 0)
            return CityHash.hash_len17_to_32(data)
        
        if length <= 64:
            return CityHash.hash_len33_to_64(data)
        
        # Handle longer strings
        x = CityHash.fetch64(data, length - 40)
        y = CityHash.fetch64(data, length - 16) + CityHash.fetch64(data, length - 56)
        z = CityHash.hash_len16(
            CityHash.fetch64(data, length - 48) + length,
            CityHash.fetch64(data, length - 24)
        )
        
        v = CityHash.weak_hash_len32_with_seeds_from_bytes(data, length - 64, length, z)
        w = CityHash.weak_hash_len32_with_seeds_from_bytes(data, length - 32, y + K1, x)
        x = CityHash._uint64(x * K1 + CityHash.fetch64(data, 0))
        
        # Process data in 64-byte chunks
        chunk_length = (len(data) - 1) & ~63
        offset = 0
        
        while chunk_length != 0:
            x = CityHash._uint64(CityHash.rotate(x + y + v[0] + CityHash.fetch64(data, offset + 8), 37) * K1)
            y = CityHash._uint64(CityHash.rotate(y + v[1] + CityHash.fetch64(data, offset + 48), 42) * K1)
            x ^= w[1]
            y = CityHash._uint64(y + v[0] + CityHash.fetch64(data, offset + 40))
            z = CityHash._uint64(CityHash.rotate(z + w[0], 33) * K1)
            
            v = CityHash.weak_hash_len32_with_seeds_from_bytes(data, offset, v[1] * K1, x + w[0])
            w = CityHash.weak_hash_len32_with_seeds_from_bytes(
                data, offset + 32, z + w[1], y + CityHash.fetch64(data, offset + 16)
            )

            z, x = x, z
            offset += 64
            chunk_length -= 64

        return CityHash.hash_len16(
            CityHash.hash_len16(v[0], w[0]) + CityHash.shift_mix(y) * K1 + z,
            CityHash.hash_len16(v[1], w[1]) + x
        )