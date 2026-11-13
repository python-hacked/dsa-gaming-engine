LANGUAGES = [
    ("python", "Python"),
    ("javascript", "JavaScript"),
    ("typescript", "TypeScript"),
    ("java", "Java"),
    ("c", "C"),
    ("cpp", "C++"),
    ("csharp", "C#"),
    ("go", "Go"),
    ("rust", "Rust"),
    ("kotlin", "Kotlin"),
    ("ruby", "Ruby"),
    ("php", "PHP"),
    ("swift", "Swift"),
]

LANGUAGE_IDS = {code for code, _name in LANGUAGES}


def editor_language(active: str | None, run_language: str) -> str:
    """The language chip wins. The marathon keeps the language it started with until then."""
    if active in LANGUAGE_IDS:
        return active
    if run_language in LANGUAGE_IDS:
        return run_language
    return "python"

DSA_GAMES = [
    {"slug": "array-swap", "title": "Array Swap Sort", "topic": "Array", "par": "90 sec"},
    {"slug": "graph-maze", "title": "Graph Maze", "topic": "Graph", "par": "2 min"},
    {"slug": "stack-brackets", "title": "Stack Brackets", "topic": "Stack", "par": "60 sec"},
    {"slug": "queue-flood", "title": "Queue Flood", "topic": "Queue", "par": "90 sec"},
    {"slug": "list-rewire", "title": "List Rewire", "topic": "Linked list", "par": "2 min"},
    {"slug": "bst-insert", "title": "BST Insert", "topic": "Tree", "par": "90 sec"},
    {"slug": "heap-extract", "title": "Heap Extract", "topic": "Heap", "par": "90 sec"},
    {"slug": "hash-frequency", "title": "Hash Frequency", "topic": "Hash map", "par": "60 sec"},
    {"slug": "two-pointers", "title": "Two Pointers", "topic": "Two pointers", "par": "90 sec"},
    {"slug": "binary-search", "title": "Binary Search", "topic": "Binary search", "par": "60 sec"},
    {"slug": "backtrack-path", "title": "Backtrack Path", "topic": "Recursion", "par": "2 min"},
    {"slug": "coin-path", "title": "Coin Path", "topic": "DP", "par": "2 min"},
    {"slug": "interval-pick", "title": "Interval Pick", "topic": "Greedy", "par": "90 sec"},
    {"slug": "trie-words", "title": "Trie Words", "topic": "Trie", "par": "90 sec"},
    {"slug": "bit-flags", "title": "Bit Flags", "topic": "Bits", "par": "60 sec"},
    {"slug": "window-string", "title": "Window String", "topic": "Sliding window", "par": "90 sec"},
    {"slug": "union-islands", "title": "Union Islands", "topic": "Union-Find", "par": "2 min"},
    {"slug": "course-order", "title": "Course Order", "topic": "Toposort", "par": "2 min"},
    {"slug": "matrix-islands", "title": "Matrix Islands", "topic": "Matrix", "par": "90 sec"},
    {"slug": "pattern-match", "title": "Pattern Match", "topic": "Strings", "par": "90 sec"},
]

SQL_TASKS = [
    {"slug": "01-pick-columns", "title": "Pick Columns", "par": "60 sec"},
    {"slug": "02-filter-rows", "title": "Filter Rows", "par": "90 sec"},
    {"slug": "03-sort-rows", "title": "Sort Rows", "par": "60 sec"},
    {"slug": "04-unique-rows", "title": "Unique Rows", "par": "60 sec"},
    {"slug": "05-count-rows", "title": "Count Rows", "par": "90 sec"},
    {"slug": "06-group-totals", "title": "Group Totals", "par": "2 min"},
    {"slug": "07-filter-groups", "title": "Filter Groups", "par": "2 min"},
    {"slug": "08-inner-join", "title": "Inner Join", "par": "2 min"},
    {"slug": "09-left-join", "title": "Left Join", "par": "2 min"},
    {"slug": "10-three-tables", "title": "Three Tables", "par": "3 min"},
    {"slug": "11-subquery", "title": "Subquery", "par": "2 min"},
    {"slug": "12-exists-match", "title": "Exists Match", "par": "2 min"},
    {"slug": "13-case-labels", "title": "Case Labels", "par": "90 sec"},
    {"slug": "14-date-buckets", "title": "Date Buckets", "par": "2 min"},
    {"slug": "15-text-match", "title": "Text Match", "par": "90 sec"},
    {"slug": "16-row-number", "title": "Row Number", "par": "2 min"},
    {"slug": "17-rank-totals", "title": "Rank Totals", "par": "3 min"},
    {"slug": "18-cte-steps", "title": "CTE Steps", "par": "3 min"},
    {"slug": "19-pick-index", "title": "Pick Index", "par": "2 min"},
    {"slug": "20-faster-query", "title": "Faster Query", "par": "3 min"},
]
