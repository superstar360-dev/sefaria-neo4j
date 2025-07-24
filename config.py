import os
from dotenv import load_dotenv
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")
EMBED_MODEL = os.getenv("EMBED_MODEL", "avichr/heBERT")
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.85"))
MIN_LENGTH = int(os.getenv("MIN_LENGTH", "50"))
USE_FAISS = os.getenv("USE_FAISS", "false").lower() == "true"
