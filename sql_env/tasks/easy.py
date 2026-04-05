from sql_env.models import SQLTask

EASY_TASKS = [
    SQLTask(
        task_id="easy_001",
        difficulty="easy",
        broken_query="SELECT * FORM users WHERE id = 1",
        canonical_answer="SELECT * FROM users WHERE id = 1",
        error_hint="There is a typo in a SQL keyword near the table name.",
    ),
    SQLTask(
        task_id="easy_002",
        difficulty="easy",
        broken_query="SELECT name, age FORM employees WHERE department = 'HR'",
        canonical_answer="SELECT name, age FROM employees WHERE department = 'HR'",
        error_hint="There is a typo in a SQL keyword near the table name.",
    ),
    SQLTask(
        task_id="easy_003",
        difficulty="easy",
        broken_query="SELECT * FROM products WEHRE price > 100",
        canonical_answer="SELECT * FROM products WHERE price > 100",
        error_hint="There is a typo in the filtering keyword.",
    ),
    SQLTask(
        task_id="easy_004",
        difficulty="easy",
        broken_query="SELCT id, name FROM customers",
        canonical_answer="SELECT id, name FROM customers",
        error_hint="There is a typo in the first keyword of the query.",
    ),
    SQLTask(
        task_id="easy_005",
        difficulty="easy",
        broken_query="SELECT COUNT(*) FORM orders WHERE status = 'pending'",
        canonical_answer="SELECT COUNT(*) FROM orders WHERE status = 'pending'",
        error_hint="There is a typo in a SQL keyword near the table name.",
    ),
]
