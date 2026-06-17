import os
from enum import IntEnum

from .city_hash import CityHash
from .crc_hash import str_crc32
from .file_io import FString
from binsl import BinReader, BinWriter

LOCMETA_MAGIC = b"\x4f\xee\x4c\xa1\x68\x48\x55\x83\x6c\x4c\x46\xbd\x70\xda\x50\x7c"


class LocmetaVersion(IntEnum):
    V0 = 0
    V1 = 1
    V2 = 2


class LocmetaFile:
    """
    Class to read and write .locmeta files.
    """

    def __init__(
        self,
        version: LocmetaVersion = LocmetaVersion.V1,
        native_culture: str = "en",
        native_locres: str = "en/Game.locres",
        compiled_cultures: list[str] = ["en"],
    ):
        self.version = version
        self.native_culture = native_culture
        self.native_locres = native_locres
        self.compiled_cultures = compiled_cultures
        self.bIsUGC = False

    def read(self, path: str):
        """
        Read a .locmeta file.

        :param path: The path to the .locmeta file to read
        """
        
        with BinReader(path) as BR:
            if BR.read(16) != LOCMETA_MAGIC:
                raise ValueError("Invalid .locmeta file")

            self.version = LocmetaVersion(BR.uint8())

            if self.version > LocmetaVersion.V1:
                raise ValueError("Unsupported .locmeta version")

            self.native_culture = FString.read(BR)
            self.native_locres = FString.read(BR)

            if self.version == LocmetaVersion.V1:
                self.compiled_cultures = BR.list(FString.read)
            else:
                self.compiled_cultures = None

            if self.version == LocmetaVersion.V2:
                self.bIsUGC = BR.bool()

    def write(self, path: str):
        """
        Write a .locmeta file.

        :param path: The path to the .locmeta file to write to
        """
        with BinWriter(path) as BW:
            BW.write(LOCMETA_MAGIC)
            BW.uint8(self.version.value)

            FString.write(BW, self.native_culture)
            FString.write(BW, self.native_locres)

            if self.version == LocmetaVersion.V1:
                BW.list(self.compiled_cultures, FString.write)

            if self.version == LocmetaVersion.V2:
                BW.bool(self.bIsUGC)
