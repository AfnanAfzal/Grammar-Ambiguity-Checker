# Grammar Ambiguity Checker

An advanced Python-based educational and compiler theory project that analyzes Context-Free Grammars (CFGs). This tool detects grammar ambiguity, generates derivations and parse trees, converts ambiguous grammars into unambiguous forms, and determines whether a grammar is deterministic using LL(1) analysis.

---

## Features

### Ambiguity Detection
- Detects whether a grammar is ambiguous
- Identifies multiple parse trees for the same input string
- Displays ambiguity results clearly

### Derivation Generation
- Generates Leftmost Derivation
- Generates Rightmost Derivation
- Displays derivation steps visually

### Parse Tree Visualization
- Generates graphical parse trees
- Displays:
  - Two trees for ambiguous grammar
  - One tree for unambiguous grammar

### Grammar Conversion
- Converts ambiguous grammar into unambiguous grammar
- Applies:
  - Operator precedence
  - Associativity rules
  - Left recursion elimination
  - Left factoring

### Determinism Checker (LL(1))
- Computes FIRST sets
- Computes FOLLOW sets
- Builds LL(1) parsing table
- Determines whether grammar is deterministic

---

## Supported Analysis

✔ Ambiguous / Unambiguous Detection  
✔ Parse Tree Generation  
✔ Leftmost Derivation  
✔ Rightmost Derivation  
✔ Grammar Transformation  
✔ Determinism Analysis (LL(1))  

---

## Example

### Input Grammar

```text
E → E+E | E*E | id
```

### Input String

```text
id+id*id
```

### Output

```text
Result:
AMBIGUOUS

Parse Trees:
Tree 1 → (id + id) * id
Tree 2 → id + (id * id)

Converted Grammar:

E → E+T | T
T → T*F | F
F → id

Determinism:
LL(1) → TRUE
```

---

## Project Structure

```text
grammar_ambiguity_checker/
│
├── main.py
├── gui.py
├── parser.py
├── ambiguity_checker.py
├── grammar_converter.py
├── determinism_checker.py
├── tree_generator.py
├── utils.py
├── requirements.txt
```

---

## Installation

Clone repository:

```bash
git clone https://github.com/YOUR_USERNAME/Grammar-Ambiguity-Checker.git
```

Go into project:

```bash
cd Grammar-Ambiguity-Checker
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run project:

```bash
python main.py
```

---

## Requirements

- Python 3.8+
- Graphviz
- NLTK
- Pillow

Install manually if needed:

```bash
pip install nltk graphviz pillow
```

---

## Technologies Used

- Python
- Tkinter
- NLTK
- Graphviz
- Compiler Design
- Context-Free Grammar (CFG)
- LL(1) Parsing

---

## Learning Outcomes

This project demonstrates concepts of:

- Compiler Construction
- Formal Languages
- Parsing Algorithms
- Grammar Transformation
- Deterministic Parsing
- Parse Tree Generation

---

## Future Improvements

- LR(0) Parser
- SLR(1) Parser
- LR(1) Parser
- LALR Parser
- Web Version (Flask/Django)
- More Grammar Optimization Techniques

---

## Author

Developed by: Afnan Afzal
