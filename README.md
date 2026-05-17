# Gramatrix

Gramatrix is an advanced, interactive desktop application built for exploring **Theory of Computation** concepts. It provides a visual and intuitive environment for designing, analyzing, and converting formal languages and automata.

## 🚀 Features

Gramatrix features a Brutalist-inspired UI and is composed of five extremely robust computational modules:

1. **Regex to Automata Engine**
   - Enter standard Regular Expressions.
   - Automatically parses and compiles to a Non-Deterministic Finite Automaton (NFA).
   - Generates equivalent Deterministic Finite Automata (DFA) and Minimal DFAs.
   - Automatically translates the language into Context-Free Grammar (CFG) production rules.

2. **DFA Canvas Designer**
   - A fully interactive, drag-and-drop visual canvas.
   - Design states (Start, Accept, Standard) and route transitions visually.
   - Dynamically calculates the equivalent Regular Expression from your visual graph using state elimination.

3. **Natural Language Processor (English Phrase Module)**
   - Type constraints in plain English (e.g., *"Strings with exactly two 'a' surrounded by zero or more 'b'"* or *"Strings with an even number of a and odd number of b"*).
   - The NLP engine interprets the semantics, processes combinations of constraints, and compiles the accurate formal Regex and Automaton on the fly.

4. **String Inference Engine**
   - Provide positive string examples (e.g., `a, aa, aaa, ...`).
   - The heuristic inference engine detects recursive sequences, extrapolates loops, and extracts the simplest mathematical Regex pattern.
   - Smoothly falls back to exact finite matching if no looping ellipsis (`...`) is provided.

5. **Context-Free Grammar (CFG) Parsing**
   - Process production rules and determine terminal/non-terminal boundaries.
   - Handles symmetric recursive rules preserving parity (like `S → aSa | Λ`) generating exact Regex outputs like `(aa)*`.
   - Visually translates the grammar into state machine approximations.

## 🛠 Prerequisites & Installation

### 1. Python Environment
Ensure you have **Python 3.12+** installed on your system.

### 2. Graphviz Installation (System-level)
The application relies on Graphviz for rendering formal state machines.
- **Windows**: Install the Graphviz executable (`graphviz_installer.exe` provided in the root, or download from the official site) and **ensure it is added to your system's PATH**.

### 3. Install Python Dependencies
Install the required packages using pip:

```bash
pip install -r requirements.txt
```

*(This includes `PyQt6` for the frontend UI and the `graphviz` python bindings).*

## 🎮 Running the Application

Execute the main module from the project root:

```bash
python src/main.py
```