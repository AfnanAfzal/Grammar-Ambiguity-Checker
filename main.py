"""
Entry point for Grammar Ambiguity Checker.
"""
import sys
sys.setrecursionlimit(15000)

from gui import GrammarAmbiguityApp

if __name__ == "__main__":
    app = GrammarAmbiguityApp()
    app.mainloop()
