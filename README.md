# Grammar Ambiguity Checker

A professional desktop application for the **Compiler Construction** course, focusing on the **Syntax Analysis Phase**.

## Features

- **Grammar Input**: Supports `->`, `→`, `=>`, `::=`, `|`, spaces, and recursion.
- **Input String Analysis**: Dynamic tokenization based on grammar terminals.
- **Ambiguity Detection**: Finds all possible parse trees for a string.
- **Leftmost & Rightmost Derivations**: Step-by-step derivation display.
- **Visual Parse Trees**: Graphical tree rendering using **Graphviz** with ASCII fallback.
- **Modern GUI**: Dark-themed Tkinter interface with custom styling.

## Installation

```bash
pip install -r requirements.txt
```

Also install Graphviz binary from [graphviz.org](https://graphviz.org/download/).

## How to Run

```bash
python main.py
```

## Project Structure

```
grammar_ambiguity_checker/
├── main.py
├── gui.py
├── parser.py
├── ambiguity_checker.py
├── tree_generator.py
├── utils.py
├── requirements.txt
└── README.md
```
