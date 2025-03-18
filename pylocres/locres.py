
from typing import Iterator
from enum import Enum

from city_hash import CityHash
from crc_hash import str_crc32
from file_io import Reader, Writer

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
        
        self._string_index = None
        

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
        """Add a namespace to the file"""
        self.namespaces[entry.name] = entry
        
    def remove(self, name: str):
        """Remove a namespace from the file"""
        del self.namespaces[name]
        
    def read(self, path):
        """Read a .locres file and fill the file object with the namespaces and entries
    
        :param path: The path to the .locres file
        """
        self.reader = Reader(path)
        self._read_header()
        
        if self.version.value >= Version.Compact.value:
            self._read_strings()
        
        self._read_keys()
        self.reader.close()
        
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
                    
                    
        
    def write(self, path):
        """Write the contents of the LocresFile to a .locres file.

        :param path: The path to the .locres file to write to
        """
        
        self.writer = Writer(path)
        
        self._write_header()
        self._make_string_dict()
        if self.version.value == Version.Legacy.value:
            self._save_legacy()
            self.writer.close()
    
    def _write_header(self):
        if self.version.value >= Version.Compact.value:
            self.writer.write(LOCRES_MAGIC)
            self.writer.uint(self.version.value)
            self.writer.write(b'\x00' * 8)
            
    def _make_string_dict(self):
        self._strings = {}
        string_count = 0
        
        for namespace in self:
            for entry in namespace:
                string = entry.translation
                
                if entry.translation in self._strings:
                    self._strings[string][0] += 1
                else:
                    self._strings.update({string: [1, string_count]})
                    string_count += 1
        
        for namespace in self:
            for entry in namespace:
                entry._string_index = self._strings[entry.translation][1]
            
            
locres = LocresFile()
namespace = Namespace("Test")
entry = Entry("key", "translation", "hash")
namespace.add(entry)
locres.add(namespace)

locres.write(r"C:\Users\Stas\Documents\GitHub\PYLocres\tests\test.locres")