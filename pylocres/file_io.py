def _is_ascii(s):
    return all(ord(c) < 128 for c in s)

class Reader:
    def __init__(self, filename: str):
        self.file = open(filename, 'rb')
    
    def set_pos(self, position: int, end=False):
        self.file.seek(-position if end else position)
    
    def read(self, size: int):
        return self.file.read(size)
        
    def uint(self):
        return int.from_bytes(self.file.read(1), byteorder='little')
    
    def uint32(self):
        return int.from_bytes(self.file.read(4), byteorder='little')
    
    def uint64(self):
        return int.from_bytes(self.file.read(8), byteorder='little')
    
    def int(self):
        return int.from_bytes(self.file.read(1), byteorder='little', signed=True)
    
    def int32(self):
        return int.from_bytes(self.file.read(4), byteorder='little', signed=True)
    
    def int64(self):
        return int.from_bytes(self.file.read(8), byteorder='little', signed=True)
    
    def string(self):
        length = self.int32()
        string = ""
        
        if length > 0:
            string = self.file.read(length).decode('ascii', errors='replace')
        elif length < 0:
            string = self.file.read(length * -2).decode('utf-16le', errors='replace')
        elif length == 0:
            string = ""
            
        return string.rstrip('\0')
    
    def close(self):
        self.file.close()
        
        
class Writer:
    def __init__(self, path):
        self.file = open(path, "wb")
        
    def set_pos(self, position: int, end=False):
        self.file.seek(-position if end else position)
        
    def write(self, data):
        self.file.write(data)
        
    def uint(self, value: int):
        self.file.write(value.to_bytes(1, 'little'))
        
    def uint32(self, value: int):
        self.file.write(value.to_bytes(4, 'little'))
        
    def uint64(self, value: int):
        self.file.write(value.to_bytes(8, 'little'))
        
    def int(self, value: int):
        self.file.write(value.to_bytes(1, 'little', signed=True))

    def int32(self, value: int):
        self.file.write(value.to_bytes(4, 'little', signed=True))
        
    def int64(self, value: int):
        self.file.write(value.to_bytes(8, 'little', signed=True))
        
    def string(self, value: str, use_unicode=False):
        value += '\x00'

        if (not use_unicode) and _is_ascii(value):
            self.uint32(len(value))
            self.write(value.encode("ascii"))
        else:
            length = int(len(value.encode("utf-16le")) / 2 * -1)
            self.int32(length)
            self.write(value.encode("utf-16le"))
            
    def close(self):
        self.file.close()