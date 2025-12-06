"""
vireon_hle_engine.py

Humanity's Last Exam (HLE) answer engine using VIREON logic:

V = Verification-weighted
I = Information-conscious
R = Recursive reasoning (multi-path)
E = Entropy-aware (disagreement as entropy)
O = Outcome-calibrated (confidence scoring)
N = Null/abstain-capable

You must plug in your own LLM backend as `llm_call` (see llm_backends.py).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Callable, Dict, Any, Tuple
import math
import time
import statistics


# LLM function type: (system_prompt, user_prompt, temperature) -> response_text
LLMFn = Callable[[str, str, float], str]


@dataclass
class VireonConfig:
    # number of independent reasoning paths
    n_paths: int = 5

    # temperature for reasoning diversity
    temperature: float = 0.7

    # follow-up verification passes per top candidate
    n_verifications: int = 2

    # weight on "information cost" in TRP-like score
    trp_lambda: float = 0.1

    # minimum confidence to give a non-null answer
    min_confidence: float = 0.55

    # allowed answer characters for multiple choice
    mc_options: str = "ABCDE"


@dataclass
class ReasoningPath:
    raw_text: str
    answer: Optional[str]
    steps: int
    info_cost: float
    verification_score: float


@dataclass
class VireonResult:
    final_answer: Optional[str]  # None => abstain / IDK
    confidence: float
    reason: str
    paths: List[ReasoningPath]
    extra: Dict[str, Any]


# ----------------------------
# Utils
# ----------------------------

def _extract_answer_token(text: str, mc_options: str) -> Optional[str]:
    """
    Heuristic: look for lines like 'Answer: X' or a single letter at end.
    """
    lower = text.lower()
    # Try explicit "answer:" pattern
    for tag in ["answer:", "final answer:", "final:", "choice:"]:
        if tag in lower:
            seg = lower.split(tag, 1)[1].strip()
            if seg:
                c = seg[0].upper()
                if c in mc_options:
                    return c

    # Fallback: last uppercase letter among options
    for ch in reversed(text.strip()):
        c = ch.upper()
        if c in mc_options:
            return c

    return None


def _count_steps(text: str) -> int:
    """
    Crude proxy for steps: number of non-trivial fragments.
    """
    fragments = []
    for part in text.replace("\n", ".").split("."):
        s = part.strip()
        if len(s) > 3:
            fragments.append(s)
    return max(1, len(fragments))


def _verification_prompt(question: str, options: Optional[List[str]], answer: str) -> str:
    """
    Ask the model to check a proposed answer, not re-solve from scratch.
    """
    opt_str = ""
    if options:
        letters = "ABCDE"
        mapped = [f"{letters[i]}. {opt}" for i, opt in enumerate(options)]
        opt_str = "\nOptions:\n" + "\n".join(mapped)

    return (
        "You are a strict verifier. You are given an exam question, its options, "
        "and a proposed answer (letter). Your job is ONLY to check if the letter "
        "is correct, NOT to come up with a new answer.\n\n"
        f"Question:\n{question}\n"
        f"{opt_str}\n\n"
        f"Proposed answer: {answer}\n\n"
        "Respond ONLY with one of:\n"
        "- CORRECT\n"
        "- INCORRECT\n"
        "- INSUFFICIENT_INFO\n"
    )


def _verification_score_from_responses(responses: List[str]) -> float:
    """
    Map verifier responses to a [0,1] score.
    """
    if not responses:
        return 0.0

    score = 0.0
    for r in responses:
        r_low = r.strip().upper()
        if "CORRECT" in r_low and "INCORRECT" not in r_low:
            score += 1.0
        elif "INCORRECT" in r_low and "CORRECT" not in r_low:
            score -= 1.0
        # INSUFFICIENT_INFO => 0

    n = len(responses)
    # Range [-n, n] → shift+scale into [0,1]
    return max(0.0, min(1.0, 0.5 + 0.5 * (score / n)))


# ----------------------------
# Core engine
# ----------------------------

class VireonHLEEngine:
    def __init__(self, llm_call: LLMFn, config: Optional[VireonConfig] = None):
        self.llm_call = llm_call
        self.cfg = config or VireonConfig()

    def answer_question(
        self,
        question: str,
        options: Optional[List[str]] = None,
    ) -> VireonResult:
        """
        Given an HLE-style question (+ optional options),
        return a VireonResult:
        - final answer letter or None if abstain
        - confidence in [0,1]
        - diagnostics (reason, path stats)
        """
        start_time = time.time()

        paths = self._generate_paths(question, options)
        self._run_verification(question, options, paths)

        final_answer, confidence, reason, extra = self._aggregate_paths(paths)

        total_time = time.time() - start_time
        extra["total_time_sec"] = total_time

        if confidence < self.cfg.min_confidence:
            return VireonResult(
                final_answer=None,
                confidence=confidence,
                reason=f"Abstain: confidence {confidence:.3f} < threshold {self.cfg.min_confidence:.3f}",
                paths=paths,
                extra=extra,
            )

        return VireonResult(
            final_answer=final_answer,
            confidence=confidence,
            reason=reason,
            paths=paths,
            extra=extra,
        )

    # ------------------------
    # Internal stages
    # ------------------------

    def _reasoning_prompt(self, question: str, options: Optional[List[str]]) -> str:
        """
        Prompt for a single reasoning path. Enforces explicit 'Answer: X'.
        """
        opt_str = ""
        if options:
            letters = "ABCDE"
            mapped = [f"{letters[i]}. {opt}" for i, opt in enumerate(options)]
            opt_str = "\nOptions (choose one):\n" + "\n".join(mapped)

        return (
            "You are taking a very difficult exam (Humanity's Last Exam).\n"
            "Think step by step, but keep the solution reasonably concise.\n"
            "At the end, output your FINAL CHOICE as a single letter from the options.\n\n"
            f"Question:\n{question}\n"
            f"{opt_str}\n\n"
            "Show your reasoning, then end with a line of the form:\n"
            "Answer: X\n"
        )

    def _generate_paths(
        self,
        question: str,
        options: Optional[List[str]],
    ) -> List[ReasoningPath]:
        paths: List[ReasoningPath] = []
        system_prompt = (
            "You are a careful, technical problem-solver trained to solve "
            "PhD-level questions. Avoid guessing; reason explicitly."
        )

        for i in range(self.cfg.n_paths):
            user_prompt = self._reasoning_prompt(question, options)
            # Stagger temperatures for diversity
            temp = max(0.1, min(1.0, self.cfg.temperature + (i - self.cfg.n_paths / 2) * 0.1))

            t0 = time.time()
            raw = self.llm_call(system_prompt, user_prompt, temp)
            dt = time.time() - t0

            ans = _extract_answer_token(raw, self.cfg.mc_options)
            steps = _count_steps(raw)
            info_cost = math.log(1.0 + steps) + dt  # simple "effort" proxy

            paths.append(
                ReasoningPath(
                    raw_text=raw,
                    answer=ans,
                    steps=steps,
                    info_cost=info_cost,
                    verification_score=0.0,
                )
            )

        return paths

    def _run_verification(
        self,
        question: str,
        options: Optional[List[str]],
        paths: List[ReasoningPath],
    ) -> None:
        """
        V = Verification-weighted: for each path with an answer,
        run an independent verifier a few times.
        """
        system_prompt = (
            "You are a strict, unemotional checker. You do not change answers; "
            "you only evaluate if a proposed letter is correct."
        )
        for p in paths:
            if p.answer is None:
                p.verification_score = 0.0
                continue

            ver_responses: List[str] = []
            for _ in range(self.cfg.n_verifications):
                v_prompt = _verification_prompt(question, options, p.answer)
                r = self.llm_call(system_prompt, v_prompt, 0.1)
                ver_responses.append(r)

            p.verification_score = _verification_score_from_responses(ver_responses)

    def _aggregate_paths(
        self,
        paths: List[ReasoningPath],
    ) -> Tuple[Optional[str], float, str, Dict[str, Any]]:
        """
        E + O + N + TRP:
        - group by answer
        - compute stability, verification, and TRP-style score
        """
        buckets: Dict[str, List[ReasoningPath]] = {}
        for p in paths:
            if p.answer is None:
                continue
            buckets.setdefault(p.answer, []).append(p)

        if not buckets:
            return None, 0.0, "No valid answers extracted from any path.", {}

        candidate_scores: Dict[str, float] = {}
        candidate_details: Dict[str, Dict[str, Any]] = {}

        total_paths = sum(len(v) for v in buckets.values())

        for ans, plist in buckets.items():
            k = len(plist)
            frac = k / total_paths

            ver_avg = statistics.mean(p.verification_score for p in plist)
            info_avg = statistics.mean(p.info_cost for p in plist)

            correctness_proxy = ver_avg
            trp_score = (correctness_proxy * frac) / (info_avg + self.cfg.trp_lambda)

            candidate_scores[ans] = trp_score
            candidate_details[ans] = {
                "paths": k,
                "frac": frac,
                "verification_avg": ver_avg,
                "info_cost_avg": info_avg,
                "trp_score": trp_score,
            }

        best_ans = max(candidate_scores, key=candidate_scores.get)
        best_score = candidate_scores[best_ans]

        scores = list(candidate_scores.values())
        if len(scores) == 1:
            confidence = min(1.0, max(0.0, 0.5 + best_score))
        else:
            s_min, s_max = min(scores), max(scores)
            if s_max == s_min:
                confidence = 0.5
            else:
                confidence = (best_score - s_min) / (s_max - s_min)

        reason = (
            f"Selected answer {best_ans} with TRP-style score {best_score:.4g}, "
            f"confidence {confidence:.3f}. Buckets: {candidate_details}"
        )

        extra = {
            "candidate_details": candidate_details,
            "candidate_scores": candidate_scores,
        }

        return best_ans, confidence, reason, extra
