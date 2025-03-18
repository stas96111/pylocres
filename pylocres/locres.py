
from typing import Iterator
from enum import Enum

import city_hash
from crc_hash import str_crc32
from file_io import Reader

LOCRES_MAGIC = b'\x0E\x14\x74\x75\x67\x4A\x03\xFC\x4A\x15\x90\x9D\xC3\x37\x7F\x1B'

class Version(Enum):
    Legacy = 0
    Compact = 1
    Optimized = 2
    CityHash = 3
        
        
class Entry():
    def __init__(self, key, translation, value, is_hash=True):
        self.key = key
        self.translation = translation
        self.hash =  value if is_hash else str_crc32(value)
        

class Namespace():
    def __init__(self, name):
        self.name = name
        self.entrys: dict[str, Entry] = {}
        
    def __iter__(self) -> Iterator[Entry]:
        return iter(self.entrys.values())
    
    def __len__(self) -> int:
        """Return the number of entries in the namespace"""
        return len(self.entrys)
    
    def __getitem__(self, index) -> Entry:
        """Allow accessing items using indexing syntax"""
        return self.entrys[index]
    
    def __repr__(self) -> str:
        return f"Namespace: [{self.name}]"
        
    def add(self, entry: Entry) -> None:
        self.entrys[entry.key] = entry
        
    def remove(self, key: str) -> None:
        del self.entrys[key]
        
        
class LocresFile:
    def __init__(self):
        self.version = Version.CityHash
        self.namespaces = {}
        
        self._offset = None
        self._strings = []
        
    def __iter__(self) -> Iterator[Namespace]:
        return iter(self.namespaces.values())
    
    def __len__(self):
        """Return the number of entries in the namespace"""
        return len(self.namespaces)
    
    def __getitem__(self, index):
        """Allow accessing items using indexing syntax"""
        return self.namespaces[index]
        
    def add(self, entry: Namespace):
        self.namespaces[entry.name] = entry
        
    def remove(self, name: str):
        del self.namespaces[name]
        
    def read(self, path):
        self.reader = Reader(path)
        self._read_header()
        
        if self.version.value >= Version.Compact.value:
            self._read_strings()
        
        self._read_keys()
        
    def _read_header(self):
        if self.reader.read(16) == LOCRES_MAGIC:
            self.version = Version(self.reader.uint())
            self._offset = self.reader.uint64()
        else:
            self.version = Version.Legacy
        
    def _read_strings(self):
        self.reader.set_pos(self._offset)
        string_count = self.reader.uint32()
        
        for i in range(string_count):
            string = self.reader.string()
            if self.version.value >= Version.Optimized.value:
                string_count = self.reader.uint32()
            self._strings.append(string)
            
    def _read_keys(self):
        if self.version.value == Version.Legacy.value:
            self.reader.set_pos(0)
        
        if self.version.value >= Version.Compact.value:
            self.reader.set_pos(25)
            
        if self.version.value >= Version.Optimized.value:
            entrys_count = self.reader.uint32()
        
        namespace_count = self.reader.uint32()
        
        for i in range(namespace_count):
            if self.version.value >= Version.Optimized.value:
                namespace_key_hash = self.reader.uint32()
                
            namespace = Namespace(self.reader.string())
            self.add(namespace)
            key_count = self.reader.uint32()
            
            for j in range(key_count):
                if self.version.value >= Version.Optimized.value:
                    string_key_hash = self.reader.uint32()
                    
                string_key = self.reader.string()
                source_string_hash = self.reader.uint32()
                
                if self.version.value >= Version.Compact.value:
                    string_index = self.reader.uint32()
                    entry = Entry(string_key, self._strings[string_index], source_string_hash)
                    namespace.add(entry)
                else:
                    translation = self.reader.string()
                    entry = Entry(string_key, translation, source_string_hash)
                    namespace.add(entry)
    