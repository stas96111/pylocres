# 🧩 PyLocres

[![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-%23313131.svg?logo=unrealengine&logoColor=white)](#)
![PyPI](https://img.shields.io/pypi/v/pylocres.svg)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pylocres)
![License](https://img.shields.io/github/license/stas96111/pylocres)
![Downloads](https://img.shields.io/pypi/dm/pylocres)

**PyLocres** is a Python library for reading, writing, and editing `.locres` and `.locmeta` files used in Unreal Engine's localization system.  
Supports **all known versions** of Locres, including the latest.

---

## 📦 Installation

Install from PyPI:

```bash
pip install pylocres
```

Or install directly from the repository:

```bash
git clone https://github.com/stas96111/pylocres.git
cd pylocres
pip install -r requirements.txt
pip install .
```

---

## 🛠️ Command Line Tool

```bash
# Show info about a .locres file
pylocres info --path example.locres

# Convert .locres to .csv
pylocres to-csv --path example.locres --out output.csv

# Convert .csv to .locres
pylocres from-csv --path output.csv --out result.locres

# Convert .locres to .po
pylocres to-po --path example.locres --out output.po

# Convert .po to .locres
pylocres from-po --path output.po --out result.locres
```

---

## 📘 Usage: Locres

```python
from pylocres import LocresFile, Namespace, Entry, LocresVersion, entry_hash

# Create Locres file instance
locres = LocresFile()

# Read a .locres file
locres.read("path/to/file.locres")

# Iterate over all namespaces
for namespace in locres:
    print("Namespace:", namespace.name or "<default>")

    # Iterate over all entries in the namespace
    for entry in namespace:
        print("Key:", entry.key) # cf433749-2e... (uuid4 or custom key)
        print("Translation:", entry.translation) # Hello world!
        print("Source Hash:", entry.hash) # 828975897

        # Set a new translation
        entry.translation = "Привіт світ!"

        # Optionally, recalculate source hash
        entry.hash = entry_hash("Hello world!")

# Create a new entry and add it to a namespace
new_entry = Entry("my_key", "My translation", entry_hash("My source"))
namespace.add(new_entry)

# Add a new namespace
new_namespace = Namespace("UI")
locres.add(new_namespace)

# Set file format version (default: CityHash)
locres.version = LocresVersion.CityHash

# Save the modified locres file
locres.write("path/to/output.locres")

# Done
```

---

## Locmeta Usage

```python
from pylocres import LocmetaFile, LocmetaVersion

# Create Locmeta file instance
locmeta = LocmetaFile()

# Read a .locmeta file
locmeta.read("path/to/file.locmeta")

# View metadata
print("Version:", locmeta.version)
print("Native culture:", locmeta.native_culture) # en
print("Native locres path:", locmeta.native_locres) # en/Game.locres
print("Compiled cultures:", locmeta.compiled_cultures) # ["en", "de", "fr", ...]

# Modify metadata
locmeta.native_culture = "uk"

# Save changes
locmeta.write("path/to/output.locmeta")

# Done
```

---
##  License
MIT License
© 2025 stas96111
