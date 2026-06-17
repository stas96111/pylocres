from binsl import BinReader, BinWriter

class FString():
    @staticmethod
    def read(BR: BinReader, length = None):
        if length is None:
            length = BR.int32()
        if length > 0:
            data = BR.read(length)
            return data.decode("ascii", errors="replace").rstrip("\0")
        elif length < 0:
            size = length * -2
            data = BR.read(size)
            return data.decode("utf-16le", errors="replace").rstrip("\0")
        else:
            return ""
    
    @staticmethod
    def write(BW: BinWriter, value: str, use_unicode: bool = False):
        value += "\x00"
        if (not use_unicode) and value.isascii():
            BW.uint32(len(value))
            BW.write(value.encode("ascii"))
        else:
            encoded = value.encode("utf-16le")
            BW.int32(-(len(encoded) // 2))
            BW.write(encoded)