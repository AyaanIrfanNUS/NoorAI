"""
NoorAI — Knowledge Base Ingestion Pipeline
Populates document_chunks table with embeddings from all Islamic sources.
Run once (or re-run to refresh a source).
"""

import os
import sys
import json
import time
import httpx
import pymupdf
import uuid
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import execute_values

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in backend/.env")
    sys.exit(1)

# ── Paths ─────────────────────────────────────────────────────────────────────
KB = Path(__file__).parent.parent / "knowledge_base"

# ── Embedding model ───────────────────────────────────────────────────────────
print("Loading embedding model (paraphrase-multilingual-mpnet-base-v2)...")
EMBEDDER = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
print("Model loaded. Output dimension:", EMBEDDER.get_embedding_dimension())
print()


def embed(text: str) -> list[float]:
    """Convert text to a 768-dimensional embedding vector."""
    return EMBEDDER.encode(text, normalize_embeddings=True).tolist()


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    doc = pymupdf.open(str(pdf_path))
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


def get_db_connection():
    """Get a psycopg2 connection, converting async-style URL if needed."""
    url = DATABASE_URL
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgresql+psycopg2://", "postgresql://")
    return psycopg2.connect(url)


def insert_chunks(conn, chunks: list[dict]) -> None:
    """Batch insert chunks into document_chunks."""
    rows = [
        (str(uuid.uuid4()), c["source_title"], c["content"], i, c["embedding"], json.dumps(c["metadata"]))
        for i, c in enumerate(chunks)
    ]
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO document_chunks (id, source_file, content, chunk_index, embedding, chunk_metadata)
            VALUES %s
            ON CONFLICT DO NOTHING
            """,
            rows,
            template="(%s::uuid, %s, %s, %s, %s::vector, %s::jsonb)"
        )
    conn.commit()
    print(f"  ✓ Inserted {len(rows)} chunks")


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 1 — QURAN (via alquran.cloud)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_quran() -> list[dict]:
    """
    Fetch all 114 surahs from alquran.cloud.
    Groups ayahs into chunks of 10 for contextual coherence.
    """
    print("Fetching Quran from alquran.cloud...")
    chunks = []

    with httpx.Client(timeout=30) as client:
        for surah_num in range(1, 115):
            arabic_resp = client.get(f"https://api.alquran.cloud/v1/surah/{surah_num}")
            english_resp = client.get(f"https://api.alquran.cloud/v1/surah/{surah_num}/en.sahih")

            if arabic_resp.status_code != 200 or english_resp.status_code != 200:
                print(f"  WARNING: Failed to fetch surah {surah_num}, skipping")
                continue

            arabic_data = arabic_resp.json()["data"]
            english_data = english_resp.json()["data"]

            surah_name = english_data["englishName"]
            surah_name_ar = arabic_data["name"]
            ayahs_ar = arabic_data["ayahs"]
            ayahs_en = english_data["ayahs"]

            group_size = 10
            for i in range(0, len(ayahs_ar), group_size):
                group_ar = ayahs_ar[i:i + group_size]
                group_en = ayahs_en[i:i + group_size]

                start_ayah = group_ar[0]["numberInSurah"]
                end_ayah = group_ar[-1]["numberInSurah"]

                english_text = " ".join(a["text"] for a in group_en)
                arabic_text = " ".join(a["text"] for a in group_ar)

                content = (
                    f"Surah {surah_name} ({surah_num}:{start_ayah}-{end_ayah})\n"
                    f"Arabic: {arabic_text}\n"
                    f"Translation: {english_text}"
                )

                chunks.append({
                    "source_title": f"Quran — Surah {surah_name}",
                    "content": content,
                    "embedding": embed(english_text),
                    "metadata": {
                        "source_type": "quran",
                        "surah_number": surah_num,
                        "surah_name": surah_name,
                        "surah_name_arabic": surah_name_ar,
                        "ayah_start": start_ayah,
                        "ayah_end": end_ayah,
                        "reference": f"{surah_num}:{start_ayah}-{end_ayah}"
                    }
                })

            time.sleep(0.3)
            if surah_num % 10 == 0:
                print(f"  Fetched surahs 1–{surah_num}...")

    print(f"  ✓ Quran: {len(chunks)} chunks from 114 surahs")
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 2 — DUAS (structured JSON — curated, not PDF-chunked)
# ─────────────────────────────────────────────────────────────────────────────

def process_duas_json() -> list[dict]:
    """
    Load duas from the curated duas_structured.json file.
    Each dua becomes exactly one chunk — no token-based chunking, since these
    are precise, scholar-verified Q&A pairs that should never be split.
    """
    json_path = KB / "duas" / "duas.json"
    print(f"Processing duas from {json_path}...")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = []
    for dua in data["duas"]:
        # What we embed: the searchable English semantic content.
        # This is what a user's question gets compared against.
        searchable_text = (
            f"{dua['title']}. "
            f"Situations: {', '.join(dua['situations'])}. "
            f"{dua['when_to_recite']}"
        )

        # What we store: the full bilingual content for display/citation.
        content = (
            f"{dua['title']}\n"
            f"Arabic: {dua['arabic']}\n"
            f"Transliteration: {dua['transliteration']}\n"
            f"Translation: {dua['translation']}\n"
            f"Source: {dua['source']}\n"
            f"When to recite: {dua['when_to_recite']}"
        )

        chunks.append({
            "source_title": f"Hisn al-Muslim / Duas Collection — {dua['collection']}",
            "content": content,
            "embedding": embed(searchable_text),
            "metadata": {
                "source_type": "dua",
                "dua_id": dua["id"],
                "collection": dua["collection"],
                "reference_number": dua["reference_number"],
                "source_reference": dua["source"],
                "situations": dua["situations"],
                "title": dua["title"]
            }
        })

    print(f"  ✓ Duas: {len(chunks)} chunks from {json_path.name}")
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# SOURCES 3-5 — PDF-BASED (prophets, seerah, fiqh)
# ─────────────────────────────────────────────────────────────────────────────

def process_stories_of_prophets() -> list[dict]:
    pdf_path = KB / "prophets" / "stories-of-the-prophets-ibn-kathir.pdf"
    print(f"Processing Stories of the Prophets from {pdf_path}...")
    raw_text = extract_pdf_text(pdf_path)
    text_chunks = chunk_text(raw_text, chunk_size=512, overlap=50)
    chunks = [
        {
            "source_title": "Stories of the Prophets (Ibn Kathir)",
            "content": c,
            "embedding": embed(c),
            "metadata": {"source_type": "prophets", "collection": "Qisas al-Anbiya",
                         "author": "Ibn Kathir", "chunk_index": i}
        }
        for i, c in enumerate(text_chunks)
    ]
    print(f" Stories of the Prophets: {len(chunks)} chunks")
    return chunks


def process_sealed_nectar() -> list[dict]:
    pdf_path = KB / "seerah" / "sealed-nectar-seerah.pdf"
    print(f"Processing The Sealed Nectar from {pdf_path}...")
    raw_text = extract_pdf_text(pdf_path)
    text_chunks = chunk_text(raw_text, chunk_size=512, overlap=50)
    chunks = [
        {
            "source_title": "The Sealed Nectar (Ar-Raheeq Al-Makhtum)",
            "content": c,
            "embedding": embed(c),
            "metadata": {"source_type": "seerah", "collection": "Ar-Raheeq Al-Makhtum",
                         "author": "Safiur Rahman Mubarakpuri", "chunk_index": i}
        }
        for i, c in enumerate(text_chunks)
    ]
    print(f"  The Sealed Nectar: {len(chunks)} chunks")
    return chunks


def process_fiqh_us_sunnah() -> list[dict]:
    pdf_path = KB / "fiqh" / "fiqh-us-sunnah.pdf"
    print(f"Processing Fiqh us-Sunnah from {pdf_path}...")
    raw_text = extract_pdf_text(pdf_path)
    text_chunks = chunk_text(raw_text, chunk_size=512, overlap=50)
    chunks = [
        {
            "source_title": "Fiqh us-Sunnah (Sayyid Sabiq)",
            "content": c,
            "embedding": embed(c),
            "metadata": {"source_type": "fiqh", "collection": "Fiqh us-Sunnah",
                         "author": "Sayyid Sabiq", "chunk_index": i}
        }
        for i, c in enumerate(text_chunks)
    ]
    print(f"  Fiqh us-Sunnah: {len(chunks)} chunks")
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

SOURCES: list[tuple[str, callable]] = [
    ("Quran", fetch_quran),
    ("Duas", process_duas_json),
    ("Stories of the Prophets", process_stories_of_prophets),
    ("Sealed Nectar", process_sealed_nectar),
    ("Fiqh us-Sunnah", process_fiqh_us_sunnah),
]

TEST_QUERY = "What is the dua for anxiety and worry?"
TEST_RESULT_LIMIT = 3


def clear_existing_chunks(conn) -> None:
    """Delete all rows from document_chunks if any exist, for a clean re-ingest."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM document_chunks")
        existing = cur.fetchone()[0]
        if existing:
            print(f"Found {existing} existing chunks — clearing for fresh ingestion...\n")
            cur.execute("DELETE FROM document_chunks")
            conn.commit()


def print_source_breakdown(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT source_file, COUNT(*)
            FROM document_chunks
            GROUP BY source_file
            ORDER BY COUNT(*) DESC
        """)
        print("\nBreakdown by source:")
        for source, count in cur.fetchall():
            print(f"  {count:>5} — {source}")


def run_test_query(conn, query: str, limit: int = TEST_RESULT_LIMIT) -> None:
    query_embedding = embed(query)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_file, content, 1 - (embedding <=> %s::vector) AS similarity
            FROM document_chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, limit),
        )
        results = cur.fetchall()

    print(f"\nTest query: '{query}'")
    for i, (source, content, similarity) in enumerate(results, 1):
        print(f"\n[{i}] {source} (similarity: {similarity:.3f})")
        print(f"    {content[:200]}...")


def main() -> None:
    print("=" * 60)
    print("NoorAI Knowledge Base Ingestion")
    print("=" * 60, "\n")

    conn = get_db_connection()
    print("✓ Connected to database\n")

    clear_existing_chunks(conn)

    total_chunks = 0
    for label, fetch_fn in SOURCES:
        chunks = fetch_fn()
        insert_chunks(conn, chunks)
        total_chunks += len(chunks)
        print()

    print("=" * 60)
    print(f"✓ Ingestion complete — {total_chunks} total chunks inserted")
    print("=" * 60)

    print_source_breakdown(conn)
    run_test_query(conn, TEST_QUERY)

    conn.close()
    print("\n✓ Done.")


if __name__ == "__main__":
    main()