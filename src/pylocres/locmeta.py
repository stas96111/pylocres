from enum import Enum

from .city_hash import CityHash
from .crc_hash import str_crc32
from .file_io import Reader, Writer

import os

LOCMETA_MAGIC = b'\x4F\xEE\x4C\xA1\x68\x48\x55\x83\x6C\x4C\x46\xBD\x70\xDA\x50\x7C'


class LocmetaFile:
    """
    Class to read and write .locmeta files.
    """
    
    class Version(Enum):
        V0 = 0
        V1 = 1

    def __init__(self, version: Version = Version.V1, native_culture: str = "en", native_locres: str = "en/Game.locres", compiled_cultures: list[str] = ["en"]):
        self.version = version
        self.native_culture = native_culture
        self.native_locres = native_locres
        self.compiled_cultures = compiled_cultures
        
    def read(self, path: str):
        """
        Read a .locmeta file.
        
        :param path: The path to the .locmeta file to read
        """
        self.reader = Reader(path)
        
        if self.reader.read(16) != LOCMETA_MAGIC:
            raise ValueError("Invalid .locmeta file")
        
        self.version = self.Version(self.reader.uint())
        
        if self.version.value > self.Version.V1.value:
            raise ValueError("Unsupported .locmeta version")
        
        self.native_culture = self.reader.string()
        self.native_locres = self.reader.string()
        
        if self.version.value == self.Version.V1.value:
            self.compiled_cultures = self.reader.strings_list()
        else:
            self.compiled_cultures = None
            
    def write(self, path: str):
        """
        Write a .locmeta file.
        
        :param path: The path to the .locmeta file to write to
        """
        self.writer = Writer(path)
        
        self.writer.write(LOCMETA_MAGIC)
        self.writer.uint(self.version.value)
        
        self.writer.string(self.native_culture)
        self.writer.string(self.native_locres)
        
        if self.version.value == self.Version.V1.value:
            self.writer.strings_list(self.compiled_cultures, True)