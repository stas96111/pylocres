# PyLocres
Python library for working with Unreal Engine .locres translation files. 

The library supports all versions of Locres

## Install
```
pip install pylocres
```
or instal from repository

## Usage

```python
    from pylocres import LocresFile, Namespace, Entry, Version, entry_hash

    # create locrese instance
    locres = LocresFile()

    # read locres file
    locres.read("./path/to/file.locres")

    # iterate over all Namespaces in locres 
    for namespace in locres:
        print(namespace.name) # print namespace name
        # Usually, the standard name is “” (empty text), so 
        # if the name is not displayed, everything is fine.

        # iterate over all Entrys in Namespace
        for entry in namespace:
            print(entry.key) # cf433749-2e... (uuid4 or custom key)
            print(entry.translation) # Hello world!
            print(entry.hash) # 828975897
            # entry.hash - source localization hash (default: English),
            # we can create our own hash if necessary, but it should be
            # replaced only when the problem is in the game itself.
            entry.hash = entry_hash("Hello world!")

            # set a new translation
            entry.translation = "Привіт світ!"

        # create new Entry
        entry = Entry(key, translation, source_hash)
        # add Entry to Namespace
        namespace.add(entry)

    # create new Namespace
    namespace = Namespace("UI")
    # add Namespace to file
    locres.add(namespace)

    # set namespace (default last version is CityHash)   
    locres.version = Version.CityHash

    # save Locres file
    locres.write("./path/to/file.locres")

    # Done
```