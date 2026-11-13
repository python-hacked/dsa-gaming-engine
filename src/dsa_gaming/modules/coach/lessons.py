LESSONS = [
    {
        "slug": "shared",
        "body": (
            "Read the board, then make the program print the same result. "
            "The language chip decides the syntax. Any correct algorithm is accepted. "
            "A hint explains the idea. A solution is the full program, and only when the player asks for it."
        ),
    },
    {
        "slug": "array-swap",
        "body": (
            "Array Swap Sort shows a row of numbers. Neighbour clicks swap two adjacent tiles. "
            "Code may sort the whole row. The program reads the numbers from stdin and prints "
            'JSON {"order": [sorted numbers]}. Selection sort and insertion sort both work.'
        ),
    },
    {
        "slug": "graph-maze",
        "body": (
            "Graph Maze is a grid. Walls block moves. The path starts at the top left and ends at the bottom right. "
            "Breadth-first search finds a short path. The program reads the grid from stdin, # for a wall and . for open, "
            'and prints JSON {"path": [[row, column], ...]}. Walk only up, down, left, and right.'
        ),
    },
    {
        "slug": "stack-brackets",
        "body": (
            "Stack Brackets gives one string of brackets. A stack remembers the opening brackets that are still unmatched. "
            "An closing bracket that does not match the top is a bad index. Leftover opening brackets are bad too. "
            "The program reads the string from stdin and prints JSON {\"bad\": [indexes]}."
        ),
    },
    {
        "slug": "queue-flood",
        "body": (
            "Queue Flood starts at the top-left open cell and spreads to open neighbours. "
            "A queue visits each open cell once, which is breadth-first search on the grid. "
            "The program reads the grid from stdin and prints JSON {\"cells\": [[row, column], ...]} "
            "for every open cell the flood can reach."
        ),
    },
]


def wants_solution(message: str) -> bool:
    text = message.lower()
    marks = (
        "solution",
        "solve",
        "full code",
        "final code",
        "complete code",
        "the code",
        "write the code",
        "give the code",
        "answer code",
        "pura code",
        "poora code",
        "code de",
        "code dedo",
        "कोड दो",
        "कोड दे",
        "पूरा कोड",
        "समाधान",
        "完整代码",
        "全部代码",
        "给我代码",
        "写出代码",
        "解决方案",
        "전체 코드",
        "코드 줘",
        "정답 코드",
        "soluction",
    )
    return any(mark in text for mark in marks)
