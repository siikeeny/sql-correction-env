import re
from sql_env.models import SQLAction, SQLTask, SQLReward


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
        'IN', 'LIKE', 'IS', 'NULL', 'DISTINCT',
    }
    normed = _normalize(query)
    found = set()
    for kw in keywords:
        if re.search(r'\b' + kw + r'\b', normed):
            found.add(kw)
    return found


def _clamp(value: float) -> float:
    """Ensure reward is strictly within (0, 1) as required by the OpenEnv spec."""
    return max(0.01, min(0.99, value))


def grade(action: SQLAction, task: SQLTask) -> SQLReward:
    """
    5-level grader with partial progress signals.
    All scores are clamped to [0.01, 0.99] — strictly between 0 and 1.

    0.99 — exact normalized match (perfect fix)
    0.70 — same token set, minor structural/whitespace differences
    0.40 — most SQL keywords correct AND high token overlap
    0.30 — partial keyword and structure match
    0.20 — basic SELECT/FROM structure present
    0.01 — not recognizable SQL
    """
    agent = _normalize(action.corrected_query)
    correct = _normalize(task.canonical_answer)

    # ── Level 1: Exact match ─────────────────────────────────────────────────
    if agent == correct:
        return SQLReward(
            value=_clamp(0.99),
            reason="Exact match — perfect correction.",
        )

    # ── Level 2: Same token set (right words, minor ordering/alias diff) ─────
    agent_tokens = _tokenize(action.corrected_query)
    correct_tokens = _tokenize(task.canonical_answer)
    if agent_tokens == correct_tokens:
        return SQLReward(
            value=_clamp(0.70),
            reason="All correct tokens present but structure differs slightly.",
        )

    # ── Level 3: Most keywords correct + high token overlap ──────────────────
    correct_kws = _sql_keywords_present(task.canonical_answer)
    agent_kws = _sql_keywords_present(action.corrected_query)
    kw_overlap = len(correct_kws & agent_kws) / max(len(correct_kws), 1)
    token_overlap = len(agent_tokens & correct_tokens) / max(len(correct_tokens), 1)

    if kw_overlap >= 0.85 and token_overlap >= 0.75:
        return SQLReward(
            value=_clamp(0.40),
            reason=(
                f"Most keywords correct "
                f"({kw_overlap:.0%} keyword match, {token_overlap:.0%} token match)."
            ),
        )

    # ── Level 3.5: Partial keyword and structure match ───────────────────────
    if kw_overlap >= 0.65 and token_overlap >= 0.50:
        return SQLReward(
            value=_clamp(0.30),
            reason=(
                f"Partial keyword and structure match "
                f"({kw_overlap:.0%} keyword match, {token_overlap:.0%} token match)."
            ),
        )

    # ── Level 4: Basic structure present ─────────────────────────────────────
    if 'SELECT' in agent and 'FROM' in agent:
        return SQLReward(
            value=_clamp(0.20),
            reason="Basic SELECT/FROM structure present but significant errors remain.",
        )

    # ── Level 0: No recognizable SQL ─────────────────────────────────────────
    return SQLReward(value=_clamp(0.01), reason="Response is not valid SQL.")


def generate_feedback(action: SQLAction, task: SQLTask, reward: SQLReward) -> str:
    """Human-readable feedback shown in the next observation."""
    if reward.value >= 0.99:
        return "Correct! Query matches perfectly."
    if reward.value >= 0.70:
        return "Very close — check spacing or minor clause differences."
    if reward.value >= 0.40:
        return (
            "Good progress — most keywords are right, "
            "but check for typos in keywords or column names."
        )
    if reward.value >= 0.30:
        return "Partial match — right direction but several keywords or columns are off."
    if reward.value >= 0.20:
        return (
            "Basic structure is there — look carefully at every SQL keyword for typos."
        )
    return "The response doesn't look like valid SQL. Start with SELECT ... FROM ..."