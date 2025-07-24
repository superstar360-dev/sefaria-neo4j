import click
import config
from ingest_explicit import ingest
from build_semantic import build
import logging
import os
import sys
from datetime import datetime

def setup_logging(command_name):
    os.makedirs('logs', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/{command_name}_{timestamp}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file

@click.group()
def cli():
    """Sefaria Graph Tools CLI"""
    pass

@cli.command("explicit")
@click.option("--refs-file", default="refs.txt", help="Path to refs.txt file with one reference per line.")
def run_explicit(refs_file):
    """Load explicit Sefaria links into Neo4j using refs file."""
    log_file = setup_logging('explicit')
    logging.info(f"Running explicit with refs_file={refs_file}")
    ingest(refs_file)
    logging.info("Explicit ingestion complete.")
    click.echo(f"? Explicit ingestion complete. Log: {log_file}")

@cli.command("semantic")
@click.option("--threshold", type=float, default=None, help="Override similarity threshold")
@click.option("--minlen", type=int, default=None, help="Override minimum text length filter")
def run_semantic(threshold, minlen):
    """Compute and load inferred semantic links."""
    log_file = setup_logging('semantic')
    if threshold is not None:
        config.SIM_THRESHOLD = threshold
        logging.info(f"Overriding SIM_THRESHOLD = {threshold}")
        click.echo(f"?? Overriding SIM_THRESHOLD = {threshold}")
    if minlen is not None:
        config.MIN_LENGTH = minlen
        logging.info(f"Overriding MIN_LENGTH = {minlen}")
        click.echo(f"?? Overriding MIN_LENGTH = {minlen}")
    build()
    logging.info("Semantic inference complete.")
    click.echo(f"? Semantic inference complete. Log: {log_file}")

if __name__ == "__main__":
    cli()
