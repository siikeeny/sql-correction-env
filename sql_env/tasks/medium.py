from sql_env.models import SQLTask
from sql_env.grader import grade

MEDIUM_TASKS = [
    SQLTask(
        task_id="medium_001",
        difficulty="medium",
        broken_query="SELECT name, SUM(salary) FORM employees GRUP BY department",
        canonical_answer="SELECT name, SUM(salary) FROM employees GROUP BY department",
        error_hint=None,
        grader=grade,
    ),
    SQLTask(
        task_id="medium_002",
        difficulty="medium",
        broken_query="SELECT * FROM orders WHER total > 500 AND status = 'active' ORDR BY total DESC",
        canonical_answer="SELECT * FROM orders WHERE total > 500 AND status = 'active' ORDER BY total DESC",
        error_hint=None,
        grader=grade,
    ),
    SQLTask(
        task_id="medium_003",
        difficulty="medium",
        broken_query="SELECT department, COUNT(*) AS emp_count FORM employees GROUP BY department HAVNG COUNT(*) > 5",
        canonical_answer="SELECT department, COUNT(*) AS emp_count FROM employees GROUP BY department HAVING COUNT(*) > 5",
        error_hint=None,
        grader=grade,
    ),
    SQLTask(
        task_id="medium_004",
        difficulty="medium",
        broken_query="SELCT product_id, SUM(quantity) FROM sales WEHRE year = 2024 GROUP BY product_id",
        canonical_answer="SELECT product_id, SUM(quantity) FROM sales WHERE year = 2024 GROUP BY product_id",
        error_hint=None,
        grader=grade,
    ),
    SQLTask(
        task_id="medium_005",
        difficulty="medium",
        broken_query="SELECT e.name, d.dept_name FORM employees e INNE JOIN departments d ON e.dept_id = d.id WHER e.salary > 50000",
        canonical_answer="SELECT e.name, d.dept_name FROM employees e INNER JOIN departments d ON e.dept_id = d.id WHERE e.salary > 50000",
        error_hint=None,
        grader=grade,
    ),
]