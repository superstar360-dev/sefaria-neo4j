from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def create_text_node(tx, tref, content_he, content_en):
    tx.run("""
        MERGE (t:Text {id: $tref})
        SET t.content_he = $content_he,
            t.content_en = $content_en
    """, tref=tref, content_he=content_he, content_en=content_en)


def create_explicit_edge(tx, src, tgt, category, commentator, anchor):
    tx.run("""
        MATCH (a:Text {id:$src}), (b:Text {id:$tgt})
        MERGE (a)-[e:EXPLICIT {
            category:$category, commentator:$commentator, anchorRef:$anchor
        }]->(b)
    """, src=src, tgt=tgt, category=category, commentator=commentator, anchor=anchor)

def create_inferred_edge(tx, src, tgt, score, method):
    tx.run("""
        MATCH (a:Text {id:$src}), (b:Text {id:$tgt})
        MERGE (a)-[e:INFERRED {
            score:$score, method:$method
        }]->(b)
    """, src=src, tgt=tgt, score=float(score), method=method)
