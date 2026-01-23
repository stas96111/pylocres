from pylocres.city_hash import CityHash
from pylocres.crc_hash import str_crc32
from pylocres import LocresFile, LocresVersion


def test_city_hash_values():

    test_cases = [
        ("", 0),
        ("I", 366061642),
        ("HI", 4113122066),
        ("List", 2316514818),
        ("Tests Tests", 2426432524),
        ("a" * 17, 3926091141),
        ("Test" * 20, 3317857492),
    ]

    for value, expected_hash in test_cases:
        result = CityHash.city_hash_64_utf16_to_uint32(value)
        assert result == expected_hash


def test_crc_hash_values():

    test_cases = [
        ("Test crc", 2908429949),
        ("Locres", 1425315323),
        ("A" * 100, 2416283133),
        ("ABC" * 100, 426380042),
    ]

    for value, expected_hash in test_cases:
        result = str_crc32(value)
        assert result == expected_hash


def test_locres_read():
    files = [
        "./tests/ver_0.locres",
        "./tests/ver_1.locres",
        "./tests/ver_2.locres",
        "./tests/ver_3.locres",
    ]

    for file in files:
        locres = LocresFile()
        locres.read(file)

        assert locres.namespaces["first"]["key_1"].translation == "first"
        assert locres.namespaces["first"]["key_2"].translation == "second"
        assert locres.namespaces["first"]["key_3"].translation == "third"
        assert locres.namespaces["second"]["key_1"].translation == "first"
        assert locres.namespaces["second"]["key_2"].translation == "second"
        assert locres.namespaces["second"]["key_3"].translation == "third"
        assert locres.namespaces["third"]["key_1"].translation == "first"
        assert locres.namespaces["third"]["key_2"].translation == "second"
        assert locres.namespaces["third"]["key_3"].translation == "third"


def test_locres_write_and_readback():
    files = {
        "./tests/ver_0.locres": LocresVersion.Legacy,
        "./tests/ver_1.locres": LocresVersion.Compact,
        "./tests/ver_2.locres": LocresVersion.CityHash,
        "./tests/ver_3.locres": LocresVersion.Optimized,
    }

    for file, version in files.items():
        locres = LocresFile()
        locres.read(file)

        temp_file = "./tests/temp.locres"
        locres.version = version
        locres.write(temp_file)

        locres_readback = LocresFile()
        locres_readback.read(temp_file)

        for namespace in locres_readback:
            for entry in namespace:
                assert (
                    entry.translation
                    == locres.namespaces[namespace.name][entry.key].translation
                )
