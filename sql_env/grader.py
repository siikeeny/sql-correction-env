import re
from sql_env.models import SQLAction, SQLTask, SQLReward


def _clamp(value: float) -> float:
    """Ensure score is strictly between 0 and 1 (gt=0.0, lt=1.0)."""
    return max(0.001, min(0.999, value))


def _normalize(query: str) -> str:
    """Uppercase, collapse whitespace, strip trailing semicolons."""
    q = query.strip().upper()
    q = re.sub(r'\s+', ' ', q)
    q = q.rstrip(';').strip()
    return q


def _tokenize(query: str) -> set:
    normed = _normalize(query)
    normed = re.sub(r"'[^']*'", '__STR__', normed)  # normalize string literals
    return set(re.findall(r"[A-Z0-9_'*.=><]+", normed))


def _sql_keywords_present(query: str) -> set:
    keywords = {
        'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'HAVING',
        'ORDER', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER',
        'BETWEEN', 'DESC', 'ASC', 'LIMIT', 'COUNT', 'SUM',
        'AVG', 'MAX', 'MIN', 'AS', 'ON', 'AND', 'OR', 'NOT',
        'IN', 'LIKE', 'IS', 'NULL', 'DISTINCT'
    }
    normed = _normalize(query)
    found = set()
    for kw in keywords:
        if re.search(r'\b' + kw + r'\b', normed):
            found.add(kw)
    return found


def grade(action: SQLAction, task: SQLTask) -> SQLReward:
    """
    4-level grader with partial progress signals.
    0.99 — exact normalized match
    0.7  — same tokens, minor whitespace/alias differences
    0.4  — key SQL keywords all present and correct table/column names
    0.2  — basic SELECT/FROM structure present
    0.01 — completely wrong
    All scores are clamped to be strictly between 0.0 and 1.0.
    """
    agent = _normalize(action.corrected_query)
    correct = _normalize(task.canonical_answer)

    # ── Level 1: Exact match ─────────────────────────────────
    if agent == correct:
        return SQLReward(
            value=_clamp(0.999),
            reason="Exact match — perfect correction."
        )

    # ── Level 2: Same token set (right words, minor ordering) ─
    agent_tokens = _tokenize(action.corrected_query)
    correct_tokens = _tokenize(task.canonical_answer)
    if agent_tokens == correct_tokens:
        return SQLReward(
            value=_clamp(0.7),
            reason="All correct tokens present but structure differs slightly."
        )

    # ── Level 3: Most keywords correct + high token overlap ───
    correct_kws = _sql_keywords_present(task.canonical_answer)
    agent_kws = _sql_keywords_present(action.corrected_query)
    kw_overlap = len(correct_kws & agent_kws) / max(len(correct_kws), 1)
    token_overlap = len(agent_tokens & correct_tokens) / max(len(correct_tokens), 1)

    if kw_overlap >= 0.85 and token_overlap >= 0.75:
        return SQLReward(
            value=_clamp(0.4),
            reason=f"Most keywords correct ({kw_overlap:.0%} keyword match, {token_overlap:.0%} token match)."
        )

    # ── Level 3.5: Partial keyword and structure match ────────
    if kw_overlap >= 0.7 and token_overlap >= 0.55:
        return SQLReward(
            value=_clamp(0.3),
            reason=f"Partial keyword and structure match ({kw_overlap:.0%} keyword match, {token_overlap:.0%} token match)."
        )

    # ── Level 4: Basic structure present ─────────────────────
    if 'SELECT' in agent and 'FROM' in agent:
        return SQLReward(
            value=_clamp(0.2),
            reason="Basic SELECT/FROM structure present but significant errors remain."
        )

    # ── Level 0: No recognizable SQL ─────────────────────────
    return SQLReward(value=_clamp(0.001), reason="Response is not valid SQL.")


def generate_feedback(action: SQLAction, task: SQLTask, reward: SQLReward) -> str:
    """Human-readable feedback shown in next observation."""
    if reward.value >= 0.99:
        return "Correct! Query matches perfectly."
    if reward.value >= 0.7:
        return "Very close — check spacing or minor clause differences."
    if reward.value >= 0.4:
        return "Good progress — most keywords are right, but check for typos in keywords or column names."
    if reward.value >= 0.3:
        return "Partial match — right direction but several keywords or columns are off."
    if reward.value >= 0.2:
        return "Basic structure is there — look carefully at every SQL keyword for typos."
    return "The response doesn't look like valid SQL. Start with SELECT ... FROM ..."