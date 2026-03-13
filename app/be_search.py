# Corpus loading and keyword search
# index built once at startup


import os
import csv
import json
from pathlib import Path

from whoosh import index
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED
from whoosh.analysis import StandardAnalyzer
from whoosh.qparser import QueryParser
from whoosh.query import Every, Term, And, Or

#add prefixes for current path, so that other things can be found relative to 
# where this file exists

# main corpus, cleaned, with no annotations
CSV_PATH = "data/cleaned_dataset.csv"
# annotated examples
ANNOTATIONS_PATH = "data/consolidated_annotations.json"
# AI annotations (Gemini)
AI_PATH = "data/Gemini_annotations_cleaned.json"
# whoosh index directory
INDEX_DIR = "whoosh_index"
# list of annotation tags
ALL_TAGS = ["all_caps", "exclamation_marks", "hedging", "adjectives", "unk"]
# index placeholder
ix = None

def make_schema():
    '''
    Defines the Whoosh index structure.

    Fields:
        doc_id: Unique document identifier for each document.
        text: Searchable text, stopwords included for hedging analysis.
        source: data source: annotated, gemini annotations or corpus (entire dataset).
        tags: 
        misinformation_label: string ID for misinformation classification.
        raw_text/raw_tags: Stored data for user interface features
    '''
    schema = Schema(
        doc_id = ID(stored=True, unique=True),
        #stoplist = None so stopwords included in search, some stopwords are in hedging lexicon
        text = TEXT(analyzer=StandardAnalyzer(stoplist=None), stored=False),
        # corpus source, for checkbox functionality
        source = ID(stored=True),
        tags = KEYWORD(stored=True, commas=False),
        misinformation_label = ID(stored=True),
        # raw text and raw tags for display, not searchability
        raw_text = STORED(),
        raw_tags = STORED()
    )  
    return schema       

def build_or_load_index():
    ''' 
    Loads the Whoosh index from disk or builds it from scratch if not found.
    
    Uses a 'Split-Set' approach during indexing to ensure the primary results 
    contain unique entries while allowing Gemini annotations to overlap for 
    comparison. 
    '''
    global ix

    if index.exists_in(INDEX_DIR): 
        print(f"[search] Loading index from '{INDEX_DIR}'")
        ix = index.open_dir(INDEX_DIR)
    else:
        print("[search] No index found... building index now")
        ix = build_index()

def build_index():
    '''
    Builds the Whoosh index by coordinating different data loaders.
    '''
    #create folder, don't throw error if folder already exists
    os.makedirs(INDEX_DIR, exist_ok=True)
    ix = create_in(INDEX_DIR, make_schema())
    writer = ix.writer()

    # 1. Main set: shared between human annotations and main corpus
    # prevents duplicates in main results
    seen_main = set()
    # 2. AI set: for Gemini/AI dataset only
    # ensures Gemini examples indexed even if they overlap with main set
    seen_ai = set()

    # pass writer and appropriate set to each function
    annotations_count = add_annotations(writer, seen_main)
    gemini_count = add_ai_annotations(writer, seen_ai)
    corpus_count = add_corpus_docs(writer, seen_main)

    writer.commit()
    print("Index built successfully!")
    print(f"  - Annotated examples: {annotations_count}")
    print(f"  - Gemini examples:    {gemini_count}")
    print(f"  - Corpus examples:    {corpus_count}")
    return ix


def add_annotations(writer, seen_main):
    '''
    Adds human-annotated examples to the index

    Parameters:
        writer: Whoosh IndexWriter object
        seen_main: set of cleaned text strings, preventing duplication
    
    Returns:
        int: total number of unique annotated examples added to index
    '''
    count = 0

    with open(ANNOTATIONS_PATH, encoding="utf-8") as file:
        examples = json.load(file)

    for i, example in enumerate(examples):
        text = example.get("Text","").strip()
        if not text or clean(text) in seen_main:
            continue
        seen_main.add(clean(text))
        # present_tags = per example flattened list of present tags
        # for whoosh search filtering
        present_tags = []
        # raw_tags = per example dict of all 5 tags with annotated text and position of annotated text
        # for front-end highlighting
        raw_tags = {}
        for tag in ALL_TAGS:
            # spans in [[word, start index, end index]] format
            spans = example.get(tag, [])
            raw_tags[tag] = spans
            if spans:
                present_tags.append(tag)
    
        writer.add_document(
            doc_id = f"annot_{i}",
            text = text,
            source = "annotated",
            tags = " ".join(present_tags),
            misinformation_label = str(example.get("misinformation_label", "")),
            raw_text = text,
            raw_tags = json.dumps(raw_tags)
        )
        count += 1

    return count


def add_ai_annotations(writer, seen_ai):
    '''
    Adds AI-generated annotations to the index.

    Parameters:
        writer: Whoosh IndexWriter object
        seen_ai: set of cleaned text strings, preventing duplication
    
    Returns:
        int: total number of AI-annotated examples added to index 
    '''
    count = 0

    with open(AI_PATH, encoding="utf-8") as file:
        examples = json.load(file)

    for i, example in enumerate(examples):
        text = example.get("Text","").strip()
        if not text or clean(text) in seen_ai:
            continue
        seen_ai.add(clean(text))
        # present_tags = per example flattened list of present tags
        # for whoosh search filtering
        present_tags = []
        # raw_tags = per example dict of all 5 tags with annotated text and position of annotated text
        # for front-end highlighting
        raw_tags = {}
        for tag in ALL_TAGS:
            # spans in [[word, start index, end index]] format
            spans = example.get(tag, [])
            raw_tags[tag] = spans
            if spans:
                present_tags.append(tag)
        writer.add_document(
            doc_id = f”ai_{int(example.get(‘ID’) or count)}“,
            text = text,
            source = "gemini",
            tags = " ".join(present_tags),
            misinformation_label = str(example.get("misinformation_label", "")),
            raw_text = text,
            raw_tags = json.dumps(raw_tags)
        )
        count += 1

    return count

def add_corpus_docs(writer, seen_main):
    ''' 
    Adds main corpus examples to the index.

    Parameters:
        writer: Whoosh IndexWriter object
        seen_main: set of cleaned text strings, preventing duplication
    
    Returns:
        int: total number of corpus examples added to index 
    '''
    count = 0
    # main corpus has no annotations, so empty raw_tags dictionary given to 
    # every example to maintain structure
    empty_tags = json.dumps({tag: [] for tag in ALL_TAGS})

    with open(CSV_PATH, encoding="utf-8", newline="") as file:
        # DictReader maps CSV headers to dictionary
        reader = csv.DictReader(file)

        for row in reader:
            text = row.get("text", "").strip()
            # use clean() helper to skip duplicates
            if not text or clean(text) in seen_main:
                continue
            seen_main.add(clean(text))

            # Handle unnamed ID column in main corpus (cleaned_dataset.csv)
            # if ID column is empty, fall back on to count
            csv_id = str(row.get("") or count)
            writer.add_document(
                doc_id = f"corpus_{csv_id}",
                text = text,
                source = "corpus",
                tags = "", 
                misinformation_label = str(row.get("label", "")),
                raw_text = text,
                raw_tags = empty_tags
                )
            count += 1

    return count 

def clean(text):
    """Lowercase and remove whitespace. Used to verify duplicates."""
    return " ".join(text.lower().split())

def search(query, 
           source="all", 
           show_ai=False, 
           tags=None, 
           misinformation_filter="all", 
           limit=50):
    '''
    Primary search function that coordinates keyword search and 
    filter-based example retrieval.

    Parameters:
        query (str): keyword search string provided by user
        source (str): data source filter ('all', 'annotated', or 'gemini')
        show_ai (bool): option to perform parallel search for AI results, default = False
        tags (list): list of annotation tags to filter by
        misinformation_filter (str): filter for label ("0", "1" or "all") default = "all"
        limit (int): maximum number of examples to return, default = 50
    
    Returns:
        dict: a dictionary containing lists of 'main_results' and, optionally, 'ai_results'
    '''
    # ensure index loaded first, otherwise error
    if ix is None:
        raise RuntimeError("Index not loaded - need to call build_or_load_index().")
    
    with ix.searcher() as searcher:
        if query.strip():
            # turn query into whoosh query object, search against text field
            text_query = QueryParser("text", ix.schema).parse(query.strip())
        else:
            # if query string is empty then search retrieves all results
            text_query = Every()
        
        # Main results (annotated and corpus)
        main_results = fetch_results(
            searcher, text_query, source, tags, misinformation_filter, limit
        )
        # AI search only runs if user checked checkbox
        ai_results = []
        if show_ai:
            ai_results = fetch_results(
                searcher, text_query, "gemini", tags, misinformation_filter, limit
            )

    return {"main_results": main_results, "ai_results": ai_results}


def fetch_results(searcher, text_query, source, tags, misinformation_filter, limit):
    '''
    Completes filtered search against Whoosh index. 
    Helper function that compiles boolean logic for source, tag 
    and misinformation label filters

    Returns:
        list: a list of dicitonaries representing the matching examples to be retrieved
    '''
    # create list of search filtering conditions 
    conditions = []

    # SOURCE filtering - annotated, gemini and/or corpus
    if source == "annotated":
        # whoosh filter, user selected annotated examples only 
        conditions.append(Term("source", "annotated"))
    elif source == "gemini":
        # user selected to include AI annotations
        conditions.append(Term("source", "gemini"))
    else:
        # default: no source specified, main corpus and annotated docs both returned
        conditions.append(Or([
            Term("source", "annotated"), 
            Term("source", "corpus")
            ]))

    # TAG filtering
    if tags:
        for tag in tags:
            conditions.append(Term("tags", tag))
    
    # MISINFORMATION LABEL filtering
    if misinformation_filter in ["0", "1"]:
        # whoosh filter, return documents that match specified misinformation label
        conditions.append(Term("misinformation_label", misinformation_filter))

    # COMPILE all user specified conditions
    if len(conditions) == 1:
        filter_query = conditions[0]
    else:
        # whoosh method And() combines conditions with "AND"
        filter_query = And(conditions)

    # perform search
    # text_query = user's keyword query, filter_query = conditions, 
    # limit is max results, defaulting to 50
    hits = searcher.search(text_query, filter=filter_query, limit=limit)

    # convert hits to a list of dictionaries
    search_results = []
    for hit in hits:
        search_results.append({
            "doc_id":               hit["doc_id"],
            "raw_text":             hit["raw_text"],
            "source":               hit["source"],
            "tags":                 hit["tags"],
            "misinformation_label": hit["misinformation_label"],
            "raw_tags":             json.loads(hit["raw_tags"]),
        })
    
    return search_results



