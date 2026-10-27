"""Safe code cleaning and lexical normalization for C/C++ source code.

Features:
- Syntax-aware state-machine comment stripper that preserves strings, chars, and URLs.
- Never uses unsafe regular expressions that corrupt string literals or escape sequences.
- Controlled whitespace normalization.
- Dedicated classical lexical baseline preparation path vs CodeBERT preservation path.
"""

from enum import Enum, auto
import re
from typing import Dict


class ParserState(Enum):
    NORMAL = auto()
    IN_STRING = auto()
    IN_CHAR = auto()
    IN_LINE_COMMENT = auto()
    IN_BLOCK_COMMENT = auto()


def safe_remove_comments(code: str, preserve_newlines: bool = True) -> str:
    """Safely strip C/C++ comments without destroying strings, character literals, or URLs.
    
    Uses a robust 5-state lexer to distinguish comments from string literals containing
    slash characters (e.g. "http://example.com" or "/* not a comment */").
    
    Args:
        code: Raw C/C++ source code string.
        preserve_newlines: When True, newlines inside comments are retained to preserve
                          line counts and formatting.
                          
    Returns:
        Code string with comments removed and strings/URLs completely preserved.
    """
    if not code:
        return ""

    result = []
    state = ParserState.NORMAL
    i = 0
    n = len(code)

    while i < n:
        char = code[i]
        next_char = code[i + 1] if i + 1 < n else ""

        if state == ParserState.NORMAL:
            if char == '"':
                state = ParserState.IN_STRING
                result.append(char)
                i += 1
            elif char == "'":
                state = ParserState.IN_CHAR
                result.append(char)
                i += 1
            elif char == "/" and next_char == "/":
                state = ParserState.IN_LINE_COMMENT
                i += 2  # skip '//'
            elif char == "/" and next_char == "*":
                state = ParserState.IN_BLOCK_COMMENT
                i += 2  # skip '/*'
            else:
                result.append(char)
                i += 1

        elif state == ParserState.IN_STRING:
            result.append(char)
            if char == "\\":
                # Escaped character inside string literal; include escaped character
                if next_char:
                    result.append(next_char)
                    i += 2
                else:
                    i += 1
            elif char == '"':
                state = ParserState.NORMAL
                i += 1
            else:
                i += 1

        elif state == ParserState.IN_CHAR:
            result.append(char)
            if char == "\\":
                # Escaped character inside char literal
                if next_char:
                    result.append(next_char)
                    i += 2
                else:
                    i += 1
            elif char == "'":
                state = ParserState.NORMAL
                i += 1
            else:
                i += 1

        elif state == ParserState.IN_LINE_COMMENT:
            if char == "\n":
                state = ParserState.NORMAL
                result.append("\n")
                i += 1
            else:
                i += 1

        elif state == ParserState.IN_BLOCK_COMMENT:
            if char == "*" and next_char == "/":
                state = ParserState.NORMAL
                i += 2  # skip '*/'
            else:
                if preserve_newlines and char == "\n":
                    result.append("\n")
                i += 1

    return "".join(result)


def normalize_whitespace(code: str) -> str:
    """Normalize excess horizontal whitespace while keeping line structure clean."""
    lines = code.splitlines()
    cleaned_lines = [re.sub(r"[ \t]+", " ", line.strip()) for line in lines]
    # Collapse empty lines
    collapsed = [line for line in cleaned_lines if line]
    return "\n".join(collapsed).strip()


def prepare_for_classical_baseline(code: str, strip_comments: bool = False) -> str:
    """Preprocess code specifically for classical lexical baselines (TF-IDF + LR/SVM).
    
    Controlled cleaning:
    - Optional safe comment removal (via state machine)
    - Normalized whitespace
    - Preserves identifiers, keywords, and structural operators
    """
    processed = code
    if strip_comments:
        processed = safe_remove_comments(processed, preserve_newlines=True)
    return normalize_whitespace(processed)


def prepare_for_codebert(code: str) -> str:
    """Preprocess code for CodeBERT deep contextual sequence classification.
    
    Strictly preserves code structure, variable identifiers, braces, indentation,
    and comments, performing only minimal safe whitespace sanitization.
    """
    if not code:
        return ""
    # CodeBERT relies on raw code syntax; only strip trailing blank margins
    return code.strip()
