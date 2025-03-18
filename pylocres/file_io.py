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
    
    def int(self):
        return int.from_bytes(self.file.read(1), byteorder='little', signed=True)
    
    def int32(self):
        return int.from_bytes(self.file.read(4), byteorder='little', signed=True)
    
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
    