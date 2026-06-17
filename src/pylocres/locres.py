from enum import IntEnum
from pathlib import Path
from typing import Iterator

from binsl import BinReader, BinWriter, Position

from .city_hash import CityHash
from .crc_hash import str_crc32
from .file_io import FString

LOCRES_MAGIC = b"\x0e\x14\x74\x75\x67\x4a\x03\xfc\x4a\x15\x90\x9d\xc3\x37\x7f\x1b"


class LocresVersion(IntEnum):
    Legacy = 0
    Compact = 1
    Optimized = 2
    CityHash = 3

class Entry:
    def __init__(self, key, translation, value, is_hash=True):
        self.key = key
        self.translation = translation
        self.hash = value if is_hash else str_crc32(value)

        self._string_index = None


class Namespace:
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
        try:
            return self.entrys[index]
        except KeyError:
            return None

    def __contains__(self, key) -> bool:
        return key in self.entrys

    def __repr__(self) -> str:
        return f"Namespace: [{self.name}]"

    def add(self, entry: Entry) -> None:
        self.entrys[entry.key] = entry

    def remove(self, key: str) -> None:
        del self.entrys[key]


class LocresFile:
    def __init__(self):
        self.version = LocresVersion.CityHash
        self.namespaces: dict[str, Namespace] = {}

        self._offset = None
        self._strings = []

    def __iter__(self) -> Iterator[Namespace]:
        return iter(self.namespaces.values())

    def __len__(self) -> int:
        """Return the number of entries in the namespace"""
        return len(self.namespaces)

    def __getitem__(self, index) -> Namespace:
        """Allow accessing items using indexing syntax"""
        try:
            return self.namespaces[index]
        except KeyError:
            return None

    def __contains__(self, key) -> bool:
        return key in self.namespaces

    def add(self, entry: Namespace):
        """Add a namespace to the file"""
        self.namespaces[entry.name] = entry

    def remove(self, name: str):
        """Remove a namespace from the file"""
        del self.namespaces[name]

    def read(self, file: str | bytes | Path):
        """Read a .locres file and fill the file object with the namespaces and entries

        :param path: The path to the .locres file
        """

        self.namespaces = {}
        self._offset = None
        self._strings = []
        
        with BinReader(file) as BR:
            self.read_header(BR)

            if self.version >= LocresVersion.Compact:
                self.read_strings(BR)

            self.read_keys(BR)

    def read_header(self, BR: BinReader):
        if BR.read(16) == LOCRES_MAGIC:
            self.version = LocresVersion(BR.uint8())
            self._offset = BR.uint64()
        else:
            self.version = LocresVersion.Legacy

    def read_strings(self, BR: BinReader):
        BR.set_pos(self._offset)
        string_count = BR.uint32()

        for i in range(string_count):
            string = FString.read(BR)
            if self.version >= LocresVersion.Optimized:
                reference_count = BR.uint32()
            self._strings.append(string)

    def read_keys(self, BR: BinReader):
        if self.version == LocresVersion.Legacy:
            BR.set_pos(0, Position.SET)

        if self.version >= LocresVersion.Compact:
            BR.set_pos(25, Position.SET)

        if self.version >= LocresVersion.Optimized:
            entrys_count = BR.uint32()

        namespace_count = BR.uint32()

        for i in range(namespace_count):
            if self.version >= LocresVersion.Optimized:
                namespace_key_hash = BR.uint32()

            namespace = Namespace(FString.read(BR))
            self.add(namespace)
            key_count = BR.uint32()

            for j in range(key_count):
                if self.version >= LocresVersion.Optimized:
                    string_key_hash = BR.uint32()

                string_key = FString.read(BR)
                source_string_hash = BR.uint32()

                if self.version >= LocresVersion.Compact:
                    string_index = BR.uint32()
                    entry = Entry(
                        string_key, self._strings[string_index], source_string_hash
                    )
                    namespace.add(entry)
                else:
                    translation = FString.read(BR)
                    entry = Entry(string_key, translation, source_string_hash)
                    namespace.add(entry)

    def to_binary(self):
        with BinWriter() as BW:
            self.write_header(BW)
            self.make_string_dict()
            if self.version == LocresVersion.Legacy:
                self.save_legacy(BW)
                return BW.get_bytes()
            self.write_keys(BW)
            self.write_text(BW)
            return BW.get_bytes()

    def write(self, file: str | Path):
        """Write the contents of the LocresFile to a .locres file.

        :param path: The path to the .locres file to write to
        """
        with BinWriter(file) as BW:
            self.write_header(BW)
            self.make_string_dict()
            if self.version == LocresVersion.Legacy:
                self.save_legacy(BW)
                return
            self.write_keys(BW)
            self.write_text(BW)

    def write_header(self, BW: BinWriter):
        if self.version >= LocresVersion.Compact:
            BW.write(LOCRES_MAGIC)
            BW.uint8(self.version.value)
            BW.write(b"\x00" * 8)

    def make_string_dict(self):
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

    def write_keys(self, BW: BinWriter):
        keys_count = 0
        for namespace in self:
            keys_count += len(namespace)
        if self.version >= LocresVersion.Optimized:
            BW.uint32(keys_count)
        BW.uint32(len(self))

        for namespace in self:
            if self.version == LocresVersion.CityHash:
                namespace_hash = CityHash.city_hash_64_utf16_to_uint32(namespace.name)
                BW.uint32(namespace_hash)
            elif self.version >= LocresVersion.Optimized:
                namespace_hash = str_crc32(namespace.name)
                BW.uint32(namespace_hash)

            FString.write(BW, namespace.name)
            BW.uint32(len(namespace))

            for entry in namespace:
                if self.version == LocresVersion.CityHash:
                    BW.uint32(CityHash.city_hash_64_utf16_to_uint32(entry.key))
                elif self.version >= LocresVersion.Optimized:
                    BW.uint32(str_crc32(entry.key))

                FString.write(BW, entry.key)
                BW.uint32(int(entry.hash))
                BW.uint32(entry._string_index)

    def write_text(self, BW: BinWriter):
        text_offset = BW.get_pos()
        with BW.at(17) as BWT: 
            BWT.uint64(text_offset)
        BW.uint32(len(self._strings))

        if self.version >= LocresVersion.Optimized:
            for string in self._strings:
                FString.write(BW, string)
                BW.uint32(self._strings[string][0])
        else:
            for string in self._strings:
                FString.write(BW, string)

    def save_legacy(self, BW: BinWriter):
        BW.uint32(len(self))

        for namespace in self:
            FString.write(BW, namespace.name, True)
            BW.uint32(len(namespace))
            for entry in namespace:
                FString.write(BW, entry.key)
                BW.uint32(entry.hash)
                FString.write(BW, entry.translation)


def entry_hash(text):
    return CityHash.city_hash_64_utf16_to_uint32(text)
