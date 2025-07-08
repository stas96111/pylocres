import click
import csv
import polib
from .locres import LocresFile, Namespace, Entry, LocresVersion


@click.group()
@click.version_option("0.1.4", prog_name="pylocres")
@click.pass_context
def cli(ctx, verbose):
    """🗂️  pylocres — A CLI tool for working with Unreal Engine .locres files"""
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose


def echo(msg, ctx=None):
    if ctx and ctx.obj.get("VERBOSE"):
        click.secho(msg, fg="yellow")


@cli.command("info", help="📄 Display metadata about the given .locres file.")
@click.option("--path", "-p", type=click.Path(exists=True), required=True, help="Path to the .locres file.")
@click.pass_context
def info(ctx, path):
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
@click.pass_context
def to_csv(ctx, path, out):
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
@click.pass_context
def from_csv(ctx, path, out, ver):
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
@click.pass_context
def to_po(ctx, path, out):
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
@click.pass_context
def from_po(ctx, path, out, ver):
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


if __name__ == "__main__":
    cli()
