---
title: SQL Correction RL Environment
emoji: 🛢️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
tags:
  - openenv
---

# SQL Correction RL Environment

An **OpenEnv-compliant** reinforcement learning environment where an AI agent
learns to fix broken SQL queries — a real task that developers face every day.

---

## Description & Motivation

SQL errors are one of the most common and costly mistakes in software development.
This environment trains agents to identify and correct SQL syntax and logical
errors, ranging from simple typos to complex multi-join query reconstruction.

The environment provides **partial progress signals** at every step — the agent
receives graded feedback even for near-correct answers, enabling meaningful
learning across the full trajectory rather than sparse end-of-episode rewards.

---

## Observation Space

| Field              | Type            | Description                                              |
|--------------------|-----------------|----------------------------------------------------------|
| `task_id`          | string          | Unique identifier for the current task instance          |
| `broken_query`     | string          | The malformed SQL query the agent must fix               |
| `schema_context`   | string or null  | Table/column definitions (provided for medium/hard tasks)|
| `error_hint`       | string or null  | Plain-language hint about the error (easy tasks only)    |
| `step_number`      | integer         | Current step within the episode                          |
| `previous_attempt` | string or null  | The agent's SQL output from the previous step            |
| `feedback`         | string or null  | Grader feedback on the previous attempt                  |

## Action Space

| Field              | Type   | Description                        |
|--------------------|--------|------------------------------------|
| `corrected_query`  | string | The agent's corrected SQL query    |

---

## Tasks

| Name     | Difficulty | Max Steps | Description |
|----------|------------|-----------|-------------|
| `easy`   | Easy       | 5         | Fix a single syntax error (e.g. `FORM` → `FROM`). Hint provided. |
| `medium` | Medium     | 6         | Fix multiple errors including missing keywords and wrong clauses. Schema provided, no hint. |
| `hard`   | Hard       | 8         | Fix complex multi-join queries with subtle errors and wrong clause ordering. Schema provided, no hint. |

---

## Reward Function

| Score | Condition |
|-------|-----------|
| `1.0` | Exact match after normalization (perfect fix) |
| `0.7` | All correct tokens present, structure slightly off |
| `0.5` | Mostly correct — small errors remain |
| `0.3` | Partial fix — several errors remain |
| `0.0` | Query still incorrect |

Episodes terminate when reward = 1.0 (success) or max_steps is reached.

---

## Setup & Usage

### Local Development

```bash
# Clone and install
git clone https://huggingface.co/spaces/YOUR_USERNAME/sql-correction-env
cd sql-correction-env
pip install -r requirements.txt

# Start the server
uvicorn server:app --host 0.0.0.0 --port 7860

# Test endpoints
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" -d '{"task_name": "easy"}'

curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"corrected_query": "SELECT * FROM users WHERE id = 1;"}'

curl -X POST http://localhost:7860/state \
  -H "Content-Type: application/json" -d '{}'
```

### Docker

```bash
docker build -t sql-correction-env .
docker run -p 7860:7860 \
  -e HF_TOKEN=your_token \
  -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
  sql-correction-env
```

### Running Inference

```bash
export HF_TOKEN=your_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export ENV_URL=http://localhost:7860

# Run each task
SQL_ENV_TASK=easy   python inference.py
SQL_ENV_TASK=medium python inference.py
SQL_ENV_TASK=hard   python inference.py
```

---

## Baseline Scores

| Task   | Model                  | Avg Score | Notes |
|--------|------------------------|-----------|-------|
| easy   | Qwen/Qwen2.5-72B       | ~0.85     | Single typo fix, hint provided |
| medium | Qwen/Qwen2.5-72B       | ~0.62     | Multi-error, schema-guided |
| hard   | Qwen/Qwen2.5-72B       | ~0.38     | Complex multi-join, no hint |

*Run `inference.py` against the live Space to reproduce these scores.*

---

## API Endpoints

| Method | Path      | Description                        |
|--------|-----------|------------------------------------|
| POST   | `/reset`  | Start new episode, returns observation |
| POST   | `/step`   | Submit action, returns result      |
| POST   | `/state`  | Get current episode state          |
| GET    | `/health` | Health check                       |
