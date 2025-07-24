import requests
from tqdm import tqdm
import os

API_BASE = "https://www.sefaria.org/api"
OUT_FILE = "sefaria_trefs.txt"

def fetch_library_index():
    """Fetch full library categories & books."""
    resp = requests.get(f"{API_BASE}/index")
    resp.raise_for_status()
    return resp.json()

def fetch_book_metadata(book_title):
    """Fetch structure of a single book (sections, lengths)."""
    resp = requests.get(f"{API_BASE}/v2/raw/index/{book_title.replace(' ', '%20')}")
    if resp.status_code == 200:
        return resp.json()
    return None

def is_real_tref(tref):
    """Check if a tref actually has text."""
    resp = requests.get(f"{API_BASE}/v3/texts/{tref}", params={"context": 0})
    return resp.ok and 'versions' in resp.json() and bool(resp.json()['versions'])

def fetch_trefs(tref):
    """Check if a tref actually has text and return the text if available, otherwise return empty list."""
    try:
        resp = requests.get(f"{API_BASE}/v3/texts/{tref}?fill_in_missing_segments=1")
        
        # Check if request was successful
        if not resp.ok:
            return []
            
        data = resp.json()
        
        # Check if 'versions' exists and is non-empty
        if 'versions' in data and data['versions']:
            # Assuming the text is in the first version
            # Note: Original code had .json() on versions which was incorrect
            return data['versions'][0].get('text', [])
            
        return []
        
    except (requests.RequestException, ValueError):
        # Handle potential request errors or JSON decode errors
        return []

def walk_books(contents):
    """Recursively yield all book nodes with a title."""
    for node in contents:
        if 'title' in node:
            yield node
        elif 'contents' in node:
            yield from walk_books(node['contents'])

def read_books_from_file(filename):
    """Read book titles from a local file, one per line."""
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def get_last_tref():
    """Get the last tref written in the output file, if exists."""
    if not os.path.exists(OUT_FILE):
        return None, None
    with open(OUT_FILE, "rb") as f:
        try:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b"\n":
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()
    if last_line.strip():
        parts = last_line.strip().split(" ")
        last_index = parts.__len__()
        
        print(parts, last_index)
        
        last_book = parts[0]
        last_indices = parts[last_index-1].split(":")

        for i in range(1,last_index-1):
            last_book += f" {parts[i]}"
        return last_book, last_indices
    return None, None

def indices_to_tref(title, indices):
    """Convert indices [1,2] ? 'BookName 1:2'"""
    return f"{title} {':'.join(map(str, indices))}"

def upgrade_chapter(indices, lengths):
    """Increment chapter and reset verse to 1"""
    indices[0] += 1
    if indices[0] > lengths[0]:  # exceeded chapter count
        return None  # end of book
    indices[-1] = 1  # reset verse to 1
    return indices



def main():
    last_book,last_indices = get_last_tref()
    print(f"?? Resuming from: {last_book} {':'.join(map(str, last_indices))}" if last_book else "?? Starting fresh")

    # Read book titles from books.txt
    book_titles = read_books_from_file('books.txt')
    resume_found = not last_book  # True if starting fresh

    with open(OUT_FILE, "a", encoding="utf-8") as out:
        for title in tqdm(book_titles, desc="Books"):
            metadata = fetch_book_metadata(title).get("schema", {})
            section_names = metadata.get("sectionNames")
            lengths = metadata.get("lengths")

            if resume_found == False:
                if title == last_book:
                    resume_found = True
                continue
            #if not (section_names and lengths):
            #    continue  # skip if no structure

            print(f"?? Processing {title}...")
            trefs_source_list = fetch_trefs(title)
            
            def create_trefs_text(indices_list, text):
                # Always write the current text (book, chapter, etc.)
                if isinstance(indices_list, list) and indices_list.__len__()>0:
                    if isinstance(indices_list[0], list):
                        for i in range(len(indices_list)):
                            create_trefs_text(indices_list[i], f"{text}:{i+1}")
                    else:
                        for i in range(len(indices_list)):
                            print_text = f"{text}:{i+1}"
                            out.write(print_text + "\n")
                            out.flush()
                else:
                    out.write(text + "\n")
                    out.flush()

            for i in range(0,trefs_source_list.__len__()):
                
                create_trefs_text(trefs_source_list[i], f"{title} {i+1}")


    print("\n? Completed writing trefs to sefaria_trefs.txt")

if __name__ == "__main__":
    main()
