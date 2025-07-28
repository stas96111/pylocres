import click
import csv
import polib
from .locres import LocresFile, Namespace, Entry, LocresVersion


@click.group()
@click.version_option("0.1.6", prog_name="pylocres")
def cli():
    """🗂️  pylocres — A CLI tool for working with Unreal Engine .locres files"""
    pass


@cli.command("info", help="📄 Display metadata about the given .locres file.")
@click.option("--path", "-p", type=click.Path(exists=True), required=True, help="Path to the .locres file.")
def info(path):
    try:
        locres = LocresFile()
        locres.read(path)

        click.secho(f"📦 Locres version: {locres.version} ({locres.version.name})", fg="green")
        click.secho(f"📚 Namespace count: {len(locres.namespaces)}", fg="green")
        click.secho(f"📝 Entries count: {sum(len(ns) for ns in locres.namespaces)}", fg="green")
    except Exception as e:
        click.secho(f"❌ Failed to read .locres file: {e}", err=True, fg="red")


@cli.command("to-csv", help="📤 Export a .locres file to a .csv file.")
@click.option("--path", "-p", type=click.Path(exists=True), required=True, help="Input .locres file path.")
@click.option("--out", "-o", type=click.Path(), default="output.csv", help="Output .csv file path.")
def to_csv(path, out):
    try:
        locres = LocresFile()
        locres.read(path)

        with open(out, 'w', newline='', encoding='utf-16le') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["namespace", "key", "hash", "source", "translation"])

            for namespace in locres:
                for entry in namespace:
                    writer.writerow([namespace.name, entry.key, entry.hash, entry.translation])

        click.secho(f"✅ CSV exported successfully to {out}", fg="green")
    except Exception as e:
        click.secho(f"❌ Error: {e}", err=True, fg="red")


@cli.command("from-csv", help="📥 Import entries from a .csv and save as a .locres file.")
@click.option("--path", "-p", type=click.Path(exists=True), required=True, help="Input .csv file path.")
@click.option("--out", "-o", type=click.Path(), default="output.locres", help="Output .locres file path.")
@click.option("--ver", "-v", type=click.IntRange(0, 3), default=3, help="Locres version (0–3).")
def from_csv(path, out, ver):
    try:
        locres = LocresFile()
        locres.version = LocresVersion(ver)

        with open(path, 'r', newline='', encoding="utf-16le") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                name = row.get("namespace", "")
                key = row.get("key")
                source_hash = row.get("hash")
                source = row.get("source") or ""
                translation = row.get("translation") or source

                namespace = locres[name] or Namespace(name)
                locres.add(namespace)
                namespace.add(Entry(key, translation, source_hash))

        locres.write(out)
        click.secho(f"✅ Locres file created at {out}", fg="green")
    except Exception as e:
        click.secho(f"❌ Error: {e}", err=True, fg="red")


@cli.command("to-po", help="📤 Convert a .locres file to a .po file (gettext format).")
@click.option("--path", "-p", type=click.Path(exists=True), required=True, help="Input .locres file path.")
@click.option("--out", "-o", type=click.Path(), default="output.po", help="Output .po file path.")
def to_po(path, out):
    try:
        locres = LocresFile()
        locres.read(path)

        pofile = polib.POFile()

        for namespace in locres:
            for entry in namespace:
                po_entry = polib.POEntry(
                    msgctxt=f"{namespace.name},{entry.key}",
                    msgid=entry.translation
                )
                pofile.append(po_entry)

        pofile.save(out)
        click.secho(f"✅ PO file exported to {out}", fg="green")
    except Exception as e:
        click.secho(f"❌ Error: {e}", err=True, fg="red")


@cli.command("from-po", help="📥 Convert a .po file to a .locres file.")
@click.option("--path", "-p", type=click.Path(exists=True), required=True, help="Input .po file path.")
@click.option("--out", "-o", type=click.Path(), default="output.locres", help="Output .locres file path.")
@click.option("--ver", "-v", type=click.IntRange(0, 3), default=3, help="Locres version (0–3).")
def from_po(path, out, ver):
    try:
        locres = LocresFile()
        locres.version = LocresVersion(ver)

        pofile = polib.pofile(path)
        for po_entry in pofile:
            try:
                name, key = po_entry.msgctxt.split(",", 1)
            except ValueError:
                click.secho(f"⚠️ Skipping entry with invalid msgctxt: {po_entry.msgctxt}", fg="yellow")
                continue

            namespace = locres[name] or Namespace(name)
            locres.add(namespace)

            translation = po_entry.msgstr or po_entry.msgid
            namespace.add(Entry(key, translation, po_entry.msgid, False))

        locres.write(out)
        click.secho(f"✅ Locres file created at {out}", fg="green")
    except Exception as e:
        click.secho(f"❌ Error: {e}", err=True, fg="red")
        
        
@cli.command("fix-hashes", help="🔧 Replace hashes in a .locres using original source language file.")
@click.option("--path", "-p", type=click.Path(exists=True), required=True, help="Path to translated or modified .locres.")
@click.option("--source_file", "-s", type=click.Path(exists=True), required=True, help="Path to original source .locres file.")
@click.option("--out", "-o", type=click.Path(), default="fixed.locres", help="Output path for updated locres.")
def fix_hashes(path, source_file, out):
    """Fixes hashes in the modified locres file using those from the source."""
    try:
        source_locres = LocresFile()
        source_locres.read(path)

        mod_locres = LocresFile()
        mod_locres.read(source_file)

        fixed = 0
        total = 0

        for mod_ns in mod_locres:
            src_ns = source_locres[mod_ns.name] if mod_ns.name in source_locres else None
            if not src_ns:
                continue

            src_entries_by_key = {e.key: e for e in src_ns}

            for mod_entry in mod_ns:
                total += 1
                src_entry = src_entries_by_key.get(mod_entry.key)
                if src_entry and mod_entry.hash != src_entry.hash:
                    mod_entry.hash = src_entry.hash
                    fixed += 1

        mod_locres.write(out)

        click.secho(f"✅ Hashes fixed: {fixed} of {total} entries updated.", fg="green")
        click.secho(f"📁 Output saved to: {out}", fg="cyan")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red", err=True)

if __name__ == "__main__":
    cli()
