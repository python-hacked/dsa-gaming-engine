import json
from string import Template

from dsa_gaming.modules.catalog.data import LANGUAGE_IDS


def _rows(walls: list[list[bool]]) -> list[str]:
    return ["".join("#" if cell else "." for cell in row) for row in walls]


def _py(items: list[str]) -> str:
    return "[" + ", ".join(repr(item) for item in items) + "]"


def _nums(tiles: list[int]) -> str:
    return ", ".join(str(number) for number in tiles)


def _quoted(items: list[str]) -> str:
    return ", ".join('"' + item + '"' for item in items)


def build_starter(slug: str, language: str, puzzle: dict) -> str:
    language = language if language in LANGUAGE_IDS else "python"
    if slug == "array-swap":
        return _ARRAY[language](puzzle["tiles"])
    if slug == "stack-brackets":
        return _STACK[language](puzzle["brackets"])
    if slug == "queue-flood":
        return _FLOOD[language](_rows(puzzle["walls"]))
    return _MAZE[language](_rows(puzzle["walls"]))


def _array_python(tiles: list[int]) -> str:
    return (
        "import json\n"
        f"tiles = {tiles}\n"
        "\n"
        "# Sort this row with any logic. The board shows the row you print.\n"
        "\n"
        'print(json.dumps({"order": tiles}))\n'
    )


def _array_javascript(tiles: list[int]) -> str:
    return (
        f"const tiles = [{_nums(tiles)}];\n"
        "\n"
        "// Sort this row with any logic. The board shows the row you print.\n"
        "\n"
        "console.log(JSON.stringify({ order: tiles }));\n"
    )


def _array_typescript(tiles: list[int]) -> str:
    return (
        f"const tiles: number[] = [{_nums(tiles)}];\n"
        "\n"
        "// Sort this row with any logic. The board shows the row you print.\n"
        "\n"
        "console.log(JSON.stringify({ order: tiles }));\n"
    )


def _array_java(tiles: list[int]) -> str:
    body = Template(
        """import java.util.*;

public class Main {
    public static void main(String[] args) {
        List<Integer> tiles = new ArrayList<>(Arrays.asList($nums));

        // Sort tiles with any logic. The board shows the row you print.

        StringBuilder out = new StringBuilder("{\\"order\\":[");
        for (int s = 0; s < tiles.size(); s++) {
            if (s > 0) out.append(",");
            out.append(tiles.get(s));
        }
        out.append("]}");
        System.out.println(out);
    }
}
"""
    )
    return body.substitute(nums=_nums(tiles))


def _array_c(tiles: list[int]) -> str:
    return Template(
        """#include <stdio.h>

int tiles[] = {$nums};
int n = $count;

int main(void) {
    /* Sort tiles with any logic. The board shows the row you print. */
    printf("{\\"order\\":[");
    for (int i = 0; i < n; i++) {
        if (i) printf(",");
        printf("%d", tiles[i]);
    }
    printf("]}\\n");
    return 0;
}
"""
    ).substitute(nums=_nums(tiles), count=len(tiles))


def _array_cpp(tiles: list[int]) -> str:
    return Template(
        """#include <iostream>
#include <vector>
using namespace std;

int main() {
    vector<int> tiles = {$nums};
    // Sort tiles with any logic. The board shows the row you print.
    cout << "{\\"order\\":[";
    for (size_t i = 0; i < tiles.size(); i++) {
        if (i) cout << ",";
        cout << tiles[i];
    }
    cout << "]}" << endl;
}
"""
    ).substitute(nums=_nums(tiles))


def _array_csharp(tiles: list[int]) -> str:
    return Template(
        """using System;
using System.Collections.Generic;

class Program {
    static void Main() {
        var tiles = new List<int> { $nums };
        // Sort tiles with any logic. The board shows the row you print.
        Console.WriteLine("{\\"order\\":[" + string.Join(",", tiles) + "]}");
    }
}
"""
    ).substitute(nums=_nums(tiles))


def _array_go(tiles: list[int]) -> str:
    return Template(
        """package main

import "fmt"

func main() {
    tiles := []int{$nums}
    // Sort tiles with any logic. The board shows the row you print.
    fmt.Print("{\\"order\\":[")
    for i, n := range tiles {
        if i > 0 {
            fmt.Print(",")
        }
        fmt.Print(n)
    }
    fmt.Println("]}")
}
"""
    ).substitute(nums=_nums(tiles))


def _array_rust(tiles: list[int]) -> str:
    return Template(
        """fn main() {
    let mut tiles = vec![$nums];
    // Sort tiles with any logic. The board shows the row you print.
    let body = tiles.iter().map(|n| n.to_string()).collect::<Vec<_>>().join(",");
    println!("{{\\"order\\":[{body}]}}");
}
"""
    ).substitute(nums=_nums(tiles))


def _array_kotlin(tiles: list[int]) -> str:
    return Template(
        """fun main() {
    val tiles = mutableListOf($nums)
    // Sort tiles with any logic. The board shows the row you print.
    println("{\\"order\\":[$${tiles.joinToString(",")}]}")
}
"""
    ).substitute(nums=_nums(tiles))


def _array_ruby(tiles: list[int]) -> str:
    return (
        "require 'json'\n"
        f"tiles = [{_nums(tiles)}]\n"
        "# Sort this row with any logic. The board shows the row you print.\n"
        "puts JSON.generate({ order: tiles })\n"
    )


def _array_php(tiles: list[int]) -> str:
    return (
        "<?php\n"
        f"$tiles = [{_nums(tiles)}];\n"
        "// Sort this row with any logic. The board shows the row you print.\n"
        "echo json_encode(['order' => $tiles]), PHP_EOL;\n"
    )


def _array_swift(tiles: list[int]) -> str:
    return Template(
        """import Foundation
var tiles = [$nums]
// Sort tiles with any logic. The board shows the row you print.
let body = tiles.map { String($$0) }.joined(separator: ",")
print("{\\"order\\":[\\(body)]}")
"""
    ).substitute(nums=_nums(tiles))


def _maze_python(rows: list[str]) -> str:
    return (
        "import json\n"
        f"grid = {_py(rows)}\n"
        "path = [[0, 0]]\n"
        "\n"
        "# '.' is open, '#' is a wall. Any logic is fine.\n"
        "# path.append([row, col]) for each step.\n"
        f"# Finish at [{len(rows) - 1}, {len(rows[0]) - 1}].\n"
        "\n"
        'print(json.dumps({"path": path}))\n'
    )


def _maze_javascript(rows: list[str]) -> str:
    return (
        f"const grid = [{_quoted(rows)}];\n"
        "const path = [[0, 0]];\n"
        "// path.push([row, col]) through '.' cells\n"
        "console.log(JSON.stringify({ path }));\n"
    )


def _maze_typescript(rows: list[str]) -> str:
    return (
        f"const grid: string[] = [{_quoted(rows)}];\n"
        "const path: number[][] = [[0, 0]];\n"
        "// path.push([row, col]) through '.' cells\n"
        "console.log(JSON.stringify({ path }));\n"
    )


def _maze_java(rows: list[str]) -> str:
    return Template(
        """import java.util.*;

public class Main {
    public static void main(String[] args) {
        String[] grid = {$rows};
        List<int[]> path = new ArrayList<>();
        path.add(new int[]{0, 0});
        // path.add(new int[]{row, col});
        StringBuilder out = new StringBuilder("{\\"path\\":[");
        for (int s = 0; s < path.size(); s++) {
            if (s > 0) out.append(",");
            out.append("[").append(path.get(s)[0]).append(",").append(path.get(s)[1]).append("]");
        }
        out.append("]}");
        System.out.println(out);
    }
}
"""
    ).substitute(rows=_quoted(rows))


def _maze_c(rows: list[str]) -> str:
    return Template(
        """#include <stdio.h>

char *grid[] = {$rows};
int rows = $count;
int path[80][2];
int pathLen = 1;

int main(void) {
    path[0][0] = 0;
    path[0][1] = 0;
    /* path[pathLen][0] = row; path[pathLen][1] = col; pathLen++; */
    printf("{\\"path\\":[");
    for (int s = 0; s < pathLen; s++) {
        if (s) printf(",");
        printf("[%d,%d]", path[s][0], path[s][1]);
    }
    printf("]}\\n");
    return 0;
}
"""
    ).substitute(rows=_quoted(rows), count=len(rows))


def _maze_cpp(rows: list[str]) -> str:
    return Template(
        """#include <iostream>
#include <vector>
#include <string>
using namespace std;

int main() {
    vector<string> grid = {$rows};
    vector<pair<int, int>> path = {{0, 0}};
    // path.push_back({row, col});
    cout << "{\\"path\\":[";
    for (size_t s = 0; s < path.size(); s++) {
        if (s) cout << ",";
        cout << "[" << path[s].first << "," << path[s].second << "]";
    }
    cout << "]}" << endl;
}
"""
    ).substitute(rows=_quoted(rows))


def _maze_csharp(rows: list[str]) -> str:
    return Template(
        """using System;
using System.Collections.Generic;
using System.Linq;

class Program {
    static void Main() {
        var grid = new[] { $rows };
        var path = new List<int[]> { new[] { 0, 0 } };
        // path.Add(new[] { row, col });
        var body = string.Join(",", path.Select(s => "[" + s[0] + "," + s[1] + "]"));
        Console.WriteLine("{\\"path\\":[" + body + "]}");
    }
}
"""
    ).substitute(rows=_quoted(rows))


def _maze_go(rows: list[str]) -> str:
    return Template(
        """package main

import ("fmt"; "strings")

func main() {
    grid := []string{$rows}
    path := [][2]int{{0, 0}}
    // path = append(path, [2]int{row, col})
    parts := []string{}
    for _, step := range path {
        parts = append(parts, fmt.Sprintf("[%d,%d]", step[0], step[1]))
    }
    fmt.Printf("{\\"path\\":[%s]}\\n", strings.Join(parts, ","))
}
"""
    ).substitute(rows=_quoted(rows))


def _maze_rust(rows: list[str]) -> str:
    quoted = ", ".join(f'"{item}".to_string()' for item in rows)
    return (
        "fn main() {\n"
        f"    let grid = vec![{quoted}];\n"
        "    let mut path = vec![(0, 0)];\n"
        "    // path.push((row, col));\n"
        '    let body = path.iter().map(|(a, b)| format!("[{a},{b}]")).collect::<Vec<_>>().join(",");\n'
        '    println!("{{\\"path\\":[{body}]}}");\n'
        "}\n"
    )


def _maze_kotlin(rows: list[str]) -> str:
    return Template(
        """fun main() {
    val grid = listOf($rows)
    val path = mutableListOf(0 to 0)
    // path.add(row to col)
    val body = path.joinToString(",") { "[$${it.first},$${it.second}]" }
    println("{\\"path\\":[$$body]}")
}
"""
    ).substitute(rows=_quoted(rows))


def _maze_ruby(rows: list[str]) -> str:
    return (
        "require 'json'\n"
        f"grid = [{_quoted(rows)}]\n"
        "path = [[0, 0]]\n"
        "# path << [row, col]\n"
        "puts JSON.generate({ path: path })\n"
    )


def _maze_php(rows: list[str]) -> str:
    return (
        "<?php\n"
        f"$grid = [{_quoted(rows)}];\n"
        "$path = [[0, 0]];\n"
        "// $path[] = [$row, $col];\n"
        "echo json_encode(['path' => $path]), PHP_EOL;\n"
    )


def _maze_swift(rows: list[str]) -> str:
    return Template(
        """import Foundation
let grid = [$rows]
var path: [[Int]] = [[0, 0]]
// path.append([row, col])
let body = path.map { "[\\($$0[0]),\\($$0[1])]" }.joined(separator: ",")
print("{\\"path\\":[\\(body)]}")
"""
    ).substitute(rows=_quoted(rows))


def _stack_python(brackets: str) -> str:
    return (
        "import json\n"
        f"brackets = {brackets!r}\n"
        "bad = []\n"
        "\n"
        "# Append the index of each bracket a stack cannot match.\n"
        "\n"
        'print(json.dumps({"bad": bad}))\n'
    )


def _stack_javascript(brackets: str) -> str:
    return (
        f"const brackets = {brackets!r};\n"
        "const bad = [];\n"
        "\n"
        "// Push the index of each bracket a stack cannot match.\n"
        "\n"
        "console.log(JSON.stringify({ bad }));\n"
    )


def _stack_typescript(brackets: str) -> str:
    return (
        f"const brackets: string = {brackets!r};\n"
        "const bad: number[] = [];\n"
        "\n"
        "// Push the index of each bracket a stack cannot match.\n"
        "\n"
        "console.log(JSON.stringify({ bad }));\n"
    )


def _dq(text: str) -> str:
    return json.dumps(text)


def _stack_java(brackets: str) -> str:
    return (
        "import java.util.*;\n\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        f"        String brackets = {_dq(brackets)};\n"
        "        List<Integer> bad = new ArrayList<>();\n"
        "\n"
        "        // bad.add(index) for each bracket a stack cannot match.\n"
        "\n"
        "        StringBuilder out = new StringBuilder(\"{\\\"bad\\\":[\");\n"
        "        for (int s = 0; s < bad.size(); s++) {\n"
        "            if (s > 0) out.append(\",\");\n"
        "            out.append(bad.get(s));\n"
        "        }\n"
        "        out.append(\"]}\");\n"
        "        System.out.println(out);\n"
        "    }\n"
        "}\n"
    )


def _stack_c(brackets: str) -> str:
    return (
        "#include <stdio.h>\n\n"
        f"char brackets[] = {_dq(brackets)};\n"
        "int bad[32];\n"
        "int badCount = 0;\n\n"
        "int main(void) {\n"
        "    /* bad[badCount++] = index; for each bracket a stack cannot match */\n"
        "    printf(\"{\\\"bad\\\":[\");\n"
        "    for (int i = 0; i < badCount; i++) {\n"
        "        if (i) printf(\",\");\n"
        "        printf(\"%d\", bad[i]);\n"
        "    }\n"
        "    printf(\"]}\\n\");\n"
        "    return 0;\n"
        "}\n"
    )


def _stack_cpp(brackets: str) -> str:
    return (
        "#include <iostream>\n"
        "#include <string>\n"
        "#include <vector>\n"
        "using namespace std;\n\n"
        "int main() {\n"
        f"    string brackets = {_dq(brackets)};\n"
        "    vector<int> bad;\n"
        "    // bad.push_back(index);\n"
        "    cout << \"{\\\"bad\\\":[\";\n"
        "    for (size_t i = 0; i < bad.size(); i++) {\n"
        "        if (i) cout << \",\";\n"
        "        cout << bad[i];\n"
        "    }\n"
        "    cout << \"]}\" << endl;\n"
        "}\n"
    )


def _stack_csharp(brackets: str) -> str:
    return (
        "using System;\n"
        "using System.Collections.Generic;\n\n"
        "class Program {\n"
        "    static void Main() {\n"
        f"        var brackets = {_dq(brackets)};\n"
        "        var bad = new List<int>();\n"
        "        // bad.Add(index);\n"
        "        Console.WriteLine(\"{\\\"bad\\\":[\" + string.Join(\",\", bad) + \"]}\");\n"
        "    }\n"
        "}\n"
    )


def _stack_go(brackets: str) -> str:
    return (
        "package main\n\n"
        "import \"fmt\"\n\n"
        "func main() {\n"
        f"    brackets := {_dq(brackets)}\n"
        "    _ = brackets\n"
        "    bad := []int{}\n"
        "    // bad = append(bad, index)\n"
        "    fmt.Print(\"{\\\"bad\\\":[\")\n"
        "    for i, n := range bad {\n"
        "        if i > 0 {\n"
        "            fmt.Print(\",\")\n"
        "        }\n"
        "        fmt.Print(n)\n"
        "    }\n"
        "    fmt.Println(\"]}\")\n"
        "}\n"
    )


def _stack_rust(brackets: str) -> str:
    return (
        "fn main() {\n"
        f"    let brackets = {_dq(brackets)};\n"
        "    let bad: Vec<usize> = Vec::new();\n"
        "    // bad.push(index);\n"
        "    let body = bad.iter().map(|n| n.to_string()).collect::<Vec<_>>().join(\",\");\n"
        "    println!(\"{{\\\"bad\\\":[{body}]}}\");\n"
        "}\n"
    )


def _stack_kotlin(brackets: str) -> str:
    return (
        "fun main() {\n"
        f"    val brackets = {_dq(brackets)}\n"
        "    val bad = mutableListOf<Int>()\n"
        "    // bad.add(index)\n"
        "    println(\"{\\\"bad\\\":[${bad.joinToString(\",\")}]}\")\n"
        "}\n"
    )


def _stack_ruby(brackets: str) -> str:
    return (
        "require 'json'\n"
        f"brackets = {brackets!r}\n"
        "bad = []\n"
        "# bad << index\n"
        "puts JSON.generate({ bad: bad })\n"
    )


def _stack_php(brackets: str) -> str:
    return (
        "<?php\n"
        f"$brackets = {brackets!r};\n"
        "$bad = [];\n"
        "// $bad[] = $index;\n"
        "echo json_encode(['bad' => $bad]), PHP_EOL;\n"
    )


def _stack_swift(brackets: str) -> str:
    return (
        "let brackets = " + _dq(brackets) + "\n"
        "var bad: [Int] = []\n"
        "// bad.append(index)\n"
        "let body = bad.map { String($0) }.joined(separator: \",\")\n"
        "print(\"{\\\"bad\\\":[\\(body)]}\")\n"
    )


def _flood_python(rows: list[str]) -> str:
    return (
        "import json\n"
        f"grid = {_py(rows)}\n"
        "cells = [[0, 0]]\n"
        "\n"
        "# '.' is open, '#' is a wall. Add every open cell the flood can reach.\n"
        "\n"
        'print(json.dumps({"cells": cells}))\n'
    )


def _flood_javascript(rows: list[str]) -> str:
    return (
        f"const grid = [{_quoted(rows)}];\n"
        "const cells = [[0, 0]];\n"
        "// Push every open cell the flood can reach.\n"
        "console.log(JSON.stringify({ cells }));\n"
    )


def _flood_typescript(rows: list[str]) -> str:
    return (
        f"const grid: string[] = [{_quoted(rows)}];\n"
        "const cells: number[][] = [[0, 0]];\n"
        "// Push every open cell the flood can reach.\n"
        "console.log(JSON.stringify({ cells }));\n"
    )


def _flood_java(rows: list[str]) -> str:
    return (
        "import java.util.*;\n\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        f"        String[] grid = {{{_quoted(rows)}}};\n"
        "        List<int[]> cells = new ArrayList<>();\n"
        "        cells.add(new int[]{0, 0});\n"
        "        // cells.add(new int[]{row, col});\n"
        "        StringBuilder out = new StringBuilder(\"{\\\"cells\\\":[\");\n"
        "        for (int s = 0; s < cells.size(); s++) {\n"
        "            if (s > 0) out.append(\",\");\n"
        "            out.append(\"[\").append(cells.get(s)[0]).append(\",\").append(cells.get(s)[1]).append(\"]\");\n"
        "        }\n"
        "        out.append(\"]}\");\n"
        "        System.out.println(out);\n"
        "    }\n"
        "}\n"
    )


def _flood_c(rows: list[str]) -> str:
    return (
        "#include <stdio.h>\n\n"
        f"char *grid[] = {{{_quoted(rows)}}};\n"
        "int cells[32][2];\n"
        "int cellCount = 1;\n\n"
        "int main(void) {\n"
        "    cells[0][0] = 0;\n"
        "    cells[0][1] = 0;\n"
        "    /* cells[cellCount][0] = row; cells[cellCount][1] = col; cellCount++; */\n"
        "    printf(\"{\\\"cells\\\":[\");\n"
        "    for (int i = 0; i < cellCount; i++) {\n"
        "        if (i) printf(\",\");\n"
        "        printf(\"[%d,%d]\", cells[i][0], cells[i][1]);\n"
        "    }\n"
        "    printf(\"]}\\n\");\n"
        "    return 0;\n"
        "}\n"
    )


def _flood_cpp(rows: list[str]) -> str:
    return (
        "#include <iostream>\n#include <string>\n#include <vector>\nusing namespace std;\n\n"
        "int main() {\n"
        f"    vector<string> grid = {{{_quoted(rows)}}};\n"
        "    vector<pair<int, int>> cells = {{0, 0}};\n"
        "    // cells.push_back({row, col});\n"
        "    cout << \"{\\\"cells\\\":[\";\n"
        "    for (size_t i = 0; i < cells.size(); i++) {\n"
        "        if (i) cout << \",\";\n"
        "        cout << \"[\" << cells[i].first << \",\" << cells[i].second << \"]\";\n"
        "    }\n"
        "    cout << \"]}\" << endl;\n"
        "}\n"
    )


def _flood_csharp(rows: list[str]) -> str:
    return (
        "using System;\nusing System.Collections.Generic;\nusing System.Linq;\n\n"
        "class Program {\n"
        "    static void Main() {\n"
        f"        var grid = new[] {{ {_quoted(rows)} }};\n"
        "        var cells = new List<int[]> { new[] { 0, 0 } };\n"
        "        // cells.Add(new[] { row, col });\n"
        "        var body = string.Join(\",\", cells.Select(s => \"[\" + s[0] + \",\" + s[1] + \"]\"));\n"
        "        Console.WriteLine(\"{\\\"cells\\\":[\" + body + \"]}\");\n"
        "    }\n"
        "}\n"
    )


def _flood_go(rows: list[str]) -> str:
    return (
        "package main\n\nimport \"fmt\"\n\nfunc main() {\n"
        f"    grid := []string{{{_quoted(rows)}}}\n"
        "    _ = grid\n"
        "    cells := [][2]int{{0, 0}}\n"
        "    // cells = append(cells, [2]int{row, col})\n"
        "    fmt.Print(\"{\\\"cells\\\":[\")\n"
        "    for i, cell := range cells {\n"
        "        if i > 0 { fmt.Print(\",\") }\n"
        "        fmt.Printf(\"[%d,%d]\", cell[0], cell[1])\n"
        "    }\n"
        "    fmt.Println(\"]}\")\n"
        "}\n"
    )


def _flood_rust(rows: list[str]) -> str:
    quoted = ", ".join(f"{_dq(item)}.to_string()" for item in rows)
    return (
        "fn main() {\n"
        f"    let grid = vec![{quoted}];\n"
        "    let cells = vec![(0, 0)];\n"
        "    // cells.push((row, col));\n"
        "    let body = cells.iter().map(|(a, b)| format!(\"[{a},{b}]\")).collect::<Vec<_>>().join(\",\");\n"
        "    println!(\"{{\\\"cells\\\":[{body}]}}\");\n"
        "}\n"
    )


def _flood_kotlin(rows: list[str]) -> str:
    return (
        "fun main() {\n"
        f"    val grid = listOf({_quoted(rows)})\n"
        "    val cells = mutableListOf(0 to 0)\n"
        "    // cells.add(row to col)\n"
        "    val body = cells.joinToString(\",\") { \"[${it.first},${it.second}]\" }\n"
        "    println(\"{\\\"cells\\\":[$body]}\")\n"
        "}\n"
    )


def _flood_ruby(rows: list[str]) -> str:
    return (
        "require 'json'\n"
        f"grid = [{_quoted(rows)}]\n"
        "cells = [[0, 0]]\n"
        "# cells << [row, col]\n"
        "puts JSON.generate({ cells: cells })\n"
    )


def _flood_php(rows: list[str]) -> str:
    return (
        "<?php\n"
        f"$grid = [{_quoted(rows)}];\n"
        "$cells = [[0, 0]];\n"
        "// $cells[] = [$row, $col];\n"
        "echo json_encode(['cells' => $cells]), PHP_EOL;\n"
    )


def _flood_swift(rows: list[str]) -> str:
    return (
        f"let grid = [{_quoted(rows)}]\n"
        "var cells: [[Int]] = [[0, 0]]\n"
        "// cells.append([row, col])\n"
        "let body = cells.map { \"[\\($0[0]),\\($0[1])]\" }.joined(separator: \",\")\n"
        "print(\"{\\\"cells\\\":[\\(body)]}\")\n"
    )


_FLOOD = {
    "python": _flood_python,
    "javascript": _flood_javascript,
    "typescript": _flood_typescript,
    "java": _flood_java,
    "c": _flood_c,
    "cpp": _flood_cpp,
    "csharp": _flood_csharp,
    "go": _flood_go,
    "rust": _flood_rust,
    "kotlin": _flood_kotlin,
    "ruby": _flood_ruby,
    "php": _flood_php,
    "swift": _flood_swift,
}

_STACK = {
    "python": _stack_python,
    "javascript": _stack_javascript,
    "typescript": _stack_typescript,
    "java": _stack_java,
    "c": _stack_c,
    "cpp": _stack_cpp,
    "csharp": _stack_csharp,
    "go": _stack_go,
    "rust": _stack_rust,
    "kotlin": _stack_kotlin,
    "ruby": _stack_ruby,
    "php": _stack_php,
    "swift": _stack_swift,
}

_ARRAY = {
    "python": _array_python,
    "javascript": _array_javascript,
    "typescript": _array_typescript,
    "java": _array_java,
    "c": _array_c,
    "cpp": _array_cpp,
    "csharp": _array_csharp,
    "go": _array_go,
    "rust": _array_rust,
    "kotlin": _array_kotlin,
    "ruby": _array_ruby,
    "php": _array_php,
    "swift": _array_swift,
}

_MAZE = {
    "python": _maze_python,
    "javascript": _maze_javascript,
    "typescript": _maze_typescript,
    "java": _maze_java,
    "c": _maze_c,
    "cpp": _maze_cpp,
    "csharp": _maze_csharp,
    "go": _maze_go,
    "rust": _maze_rust,
    "kotlin": _maze_kotlin,
    "ruby": _maze_ruby,
    "php": _maze_php,
    "swift": _maze_swift,
}
