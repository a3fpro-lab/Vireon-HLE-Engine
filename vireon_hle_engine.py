from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional


# Type of the LLM call function: (system_prompt, user_prompt, temperature) -> response text
LLMCall = Callable[[str, str, float], str]


@dataclass
class VireonConfig:
    """
    Configuration for the Vireon HLE engine.
    """

    n_paths: int = 6
    temperature: float = 0.6
    n_verifications: int = 3
    trp_lambda: float = 0.12
    min_confidence: float = 0.60
    mc_options: str = "ABCDE"


@dataclass
class VireonResult:
    """
    Result of answering a single question.
    """

    final_answer: Optional[str]
    confidence: float
    reason: str


class VireonHLEEngine:
    """
    Simple Vireon-style engine for HLE-style multiple-choice questions.

    For now, this is a clean, minimal implementation:
    - one LLM call per question
    - extracts a single letter (A–E) or abstains
    - assigns a basic confidence score

    Later you can extend this to:
    - multiple reasoning paths
    - verification passes
    - TRP-based aggregation
    """

    def __init__(self, llm_call: LLMCall, config: VireonConfig):
        self.llm_call = llm_call
        self.config = config

    # --------------------------------------------------------
    # Prompt building
    # --------------------------------------------------------
    def _build_system_prompt(self) -> str:
        return (
            "You are Vireon, a careful exam reasoning engine.\n"
            "You receive hard multiple-choice questions.\n"
            "You must think step by step, but in the final answer "
            "you ONLY output a single letter (A, B, C, D, or E), "
            "or the word ABSTAIN if you truly cannot decide.\n"
        )

    def _build_user_prompt(self, question: str, options: Optional[List[str]]) -> str:
        if options:
            lines: List[str] = [question, "", "Options:"]
            letters = self.config.mc_options
            for i, opt in enumerate(options):
                if i < len(letters):
                    lines.append(f"{letters[i]}. {opt}")
            lines.append("")
            lines.append(
                "First, think carefully and compare the options.\n"
                "Then on the last line, answer with ONLY the letter of the best option "
                "(A, B, C, D, or E), or ABSTAIN if you are not confident."
            )
            return "\n".join(lines)
        else:
            return (
                question
                + "\n\nThink carefully, then answer concisely. "
                "If you are not confident, answer with the single word: ABSTAIN."
            )

    # --------------------------------------------------------
    # Output parsing
    # --------------------------------------------------------
    def _extract_letter(self, raw: str) -> Optional[str]:
        """
        Extract a letter A–E or abstain from the model's raw text.
        Returns:
            - 'A'..'E' if a clear letter is found
            - None if the model abstains or we can't parse a letter
        """
        if not raw:
            return None

        txt = raw.strip().upper()

        # If it explicitly says ABSTAIN anywhere, treat as abstain
        if "ABSTAIN" in txt:
            return None

        # Look for the first A–E in the text
        for ch in txt:
            if ch in self.config.mc_options:
                return ch

        return None

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------
    def answer_question(self, question: str, options: Optional[List[str]]) -> VireonResult:
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(question, options)

        # Single-call baseline; future: multiple paths + verification
        raw = self.llm_call(system_prompt, user_prompt, self.config.temperature)

        if options:
            letter = self._extract_letter(raw)
        else:
            # For non-MC questions, you could later return free-form answers.
            # For now, treat as abstain unless extended.
            letter = None

        # Very simple confidence heuristic:
        # - 0.8 if we got a letter
        # - 0.0 otherwise
        conf = 0.8 if letter is not None else 0.0

        if letter is None or conf < self.config.min_confidence:
            # Abstain
            return VireonResult(
                final_answer=None,
                confidence=conf,
                reason=raw or "",
            )

        # Confident MC answer
        return VireonResult(
            final_answer=letter,
            confidence=conf,
            reason=raw or "",
        )
