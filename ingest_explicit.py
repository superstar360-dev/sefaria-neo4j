from sefaria_api import fetch_links, fetch_text
from neo4j_io import driver, create_text_node, create_explicit_edge
from tqdm import tqdm
import logging

def get_refs_from_file(path="sefaria_trefs.txt"):
    with open(path, encoding="utf8") as f:
        return [line.strip() for line in f if line.strip()]

def ingest(refs_path="sefaria_trefs.txt"):
    refs = get_refs_from_file(refs_path)
    for ref in tqdm(refs, desc="?? Ingesting Texts"):
        try:
            text = fetch_text(ref).get("versions",[])
            he = text[0]["text"]
            en = text[1]["text"]

            with driver.session() as sess:
                sess.write_transaction(create_text_node, ref, he, en)

            links = fetch_links(ref)
            for link in tqdm(links, desc=f"?? Links for {ref}", leave=False):
                src = link.get("anchorRef")
                tgt = link.get("ref")
                tgthe = link.get("he", "")
                tgten = link.get("text", "")
                if src and tgt:
                    with driver.session() as sess:
                        sess.write_transaction(create_text_node, tgt, tgthe, tgten)
                        sess.write_transaction(
                            create_explicit_edge,
                            src,
                            tgt,
                            link.get("category", ""),
                            link.get("commentator", ""),
                            src
                        )
        except Exception as e:
            logging.error(f"Error processing {ref}: {e}")