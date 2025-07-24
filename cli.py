import click
import config
from ingest_explicit import ingest
from build_semantic import build

@click.group()
def cli():
    """Sefaria Graph Tools CLI"""
    pass

@cli.command("explicit")
@click.option("--refs-file", default="refs.txt", help="Path to refs.txt file with one reference per line.")
def run_explicit(refs_file):
    """Load explicit Sefaria links into Neo4j using refs file."""
    ingest(refs_file)
    click.echo("? Explicit ingestion complete.")

@cli.command("semantic")
@click.option("--threshold", type=float, default=None, help="Override similarity threshold")
@click.option("--minlen", type=int, default=None, help="Override minimum text length filter")
def run_semantic(threshold, minlen):
    """Compute and load inferred semantic links."""
    if threshold is not None:
        config.SIM_THRESHOLD = threshold
        click.echo(f"?? Overriding SIM_THRESHOLD = {threshold}")
    if minlen is not None:
        config.MIN_LENGTH = minlen
        click.echo(f"?? Overriding MIN_LENGTH = {minlen}")

    build()
    click.echo("? Semantic inference complete.")

if __name__ == "__main__":
    cli()
