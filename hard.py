from sql_env.models import SQLTask

HARD_TASKS = [
    SQLTask(
        task_id="hard_001",
        difficulty="hard",
        broken_query="SELCT e.name, d.dept_name, SUM(s.amount) AS total_sales FORM employees e LFT JOIN departments d ON e.dpt_id = d.id INNE JOIN sales s ON e.id = s.emp_id WHER s.sale_date BETWEN '2024-01-01' AND '2024-12-31' GRUP BY e.name, d.dept_name HAVNG SUM(s.amount) > 10000 ORDR BY total_sales DSC",
        canonical_answer="SELECT e.name, d.dept_name, SUM(s.amount) AS total_sales FROM employees e LEFT JOIN departments d ON e.dept_id = d.id INNER JOIN sales s ON e.id = s.emp_id WHERE s.sale_date BETWEEN '2024-01-01' AND '2024-12-31' GROUP BY e.name, d.dept_name HAVING SUM(s.amount) > 10000 ORDER BY total_sales DESC",
        schema_context=(
            "employees(id INT, name VARCHAR, dept_id INT, salary DECIMAL)\n"
            "departments(id INT, dept_name VARCHAR)\n"
            "sales(id INT, emp_id INT, amount DECIMAL, sale_date DATE)"
        ),
        error_hint=None,
        max_steps=4,
    ),
    SQLTask(
        task_id="hard_002",
        difficulty="hard",
        broken_query="SELECT c.name, COUNT(o.id) AS order_count, SUM(oi.qty * p.price) AS revenue FORM customers c LFT JOIN orders o ON c.id = o.customer_id LFT JOIN order_items oi ON o.id = oi.order_id INNE JOIN products p ON oi.product_id = p.id WHER o.created_at >= '2024-01-01' GRUP BY c.name HAVNG revenue > 5000 ORDR BY revenue DSC LIMT 10",
        canonical_answer="SELECT c.name, COUNT(o.id) AS order_count, SUM(oi.qty * p.price) AS revenue FROM customers c LEFT JOIN orders o ON c.id = o.customer_id LEFT JOIN order_items oi ON o.id = oi.order_id INNER JOIN products p ON oi.product_id = p.id WHERE o.created_at >= '2024-01-01' GROUP BY c.name HAVING revenue > 5000 ORDER BY revenue DESC LIMIT 10",
        schema_context=(
            "customers(id INT, name VARCHAR, email VARCHAR)\n"
            "orders(id INT, customer_id INT, created_at DATETIME)\n"
            "order_items(id INT, order_id INT, product_id INT, qty INT)\n"
            "products(id INT, name VARCHAR, price DECIMAL)"
        ),
        error_hint=None,
        max_steps=4,
    ),
    SQLTask(
        task_id="hard_003",
        difficulty="hard",
        broken_query="SELECT dept, AVG(salary) AS avg_sal, MAX(salary) AS max_sal FORM employees WHER hire_date BETWEN '2020-01-01' AND '2023-12-31' AND status = 'active' GRUP BY dept HAVNG AVG(salary) > 60000 ORDR BY avg_sal DSC",
        canonical_answer="SELECT dept, AVG(salary) AS avg_sal, MAX(salary) AS max_sal FROM employees WHERE hire_date BETWEEN '2020-01-01' AND '2023-12-31' AND status = 'active' GROUP BY dept HAVING AVG(salary) > 60000 ORDER BY avg_sal DESC",
        schema_context=(
            "employees(id INT, name VARCHAR, dept VARCHAR, salary DECIMAL, hire_date DATE, status VARCHAR)"
        ),
        error_hint=None,
        max_steps=4,
    ),
]
