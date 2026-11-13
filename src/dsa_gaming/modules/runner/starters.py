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
