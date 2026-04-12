from sql_env.models import SQLTask
from sql_env.grader import grade

HARD_TASKS = [
    SQLTask(
        task_id="hard_001",
        difficulty="hard",
        broken_query=(
            "SELCT e.name, d.dept_name, SUM(s.amount) AS total_sales "
            "FORM employees e LFT JOIN departments d ON e.dpt_id = d.id "
            "INNE JOIN sales s ON e.id = s.emp_id "
            "WHER s.sale_date BETWEN '2024-01-01' AND '2024-12-31' "
            "GRUP BY e.name, d.dept_name "
            "HAVNG SUM(s.amount) > 10000 "
            "ORDR BY total_sales DSC"
        ),
        canonical_answer=(
            "SELECT e.name, d.dept_name, SUM(s.amount) AS total_sales "
            "FROM employees e LEFT JOIN departments d ON e.dept_id = d.id "
            "INNER JOIN sales s ON e.id = s.emp_id "
            "WHERE s.sale_date BETWEEN '2024-01-01' AND '2024-12-31' "
            "GROUP BY e.name, d.dept_name "
            "HAVING SUM(s.amount) > 10000 "
            "ORDER BY total_sales DESC"
        ),
        schema_context=(
            "employees(id INT, name VARCHAR, dept_id INT, salary DECIMAL)\n"
            "departments(id INT, dept_name VARCHAR)\n"
            "sales(id INT, emp_id INT, amount DECIMAL, sale_date DATE)"
        ),
        error_hint=None,
        max_steps=4,
        grader=grade,
    ),
    SQLTask(
        task_id="hard_002",
        difficulty="hard",
        broken_query=(
            "SELECT c.name, COUNT(o.id) AS order_count, SUM(oi.qty * p.price) AS revenue "
            "FORM customers c LFT JOIN orders o ON c.id = o.customer_id "
            "LFT JOIN order_items oi ON o.id = oi.order_id "
            "INNE JOIN products p ON oi.product_id = p.id "
            "WHER o.created_at >= '2024-01-01' "
            "GRUP BY c.name "
            "HAVNG revenue > 5000 "
            "ORDR BY revenue DSC LIMT 10"
        ),
        canonical_answer=(
            "SELECT c.name, COUNT(o.id) AS order_count, SUM(oi.qty * p.price) AS revenue "
            "FROM customers c LEFT JOIN orders o ON c.id = o.customer_id "
            "LEFT JOIN order_items oi ON o.id = oi.order_id "
            "INNER JOIN products p ON oi.product_id = p.id "
            "WHERE o.created_at >= '2024-01-01' "
            "GROUP BY c.name "
            "HAVING revenue > 5000 "
            "ORDER BY revenue DESC LIMIT 10"
        ),
        schema_context=(
            "customers(id INT, name VARCHAR, email VARCHAR)\n"
            "orders(id INT, customer_id INT, created_at DATETIME)\n"
            "order_items(id INT, order_id INT, product_id INT, qty INT)\n"
            "products(id INT, name VARCHAR, price DECIMAL)"
        ),
        error_hint=None,
        max_steps=4,
        grader=grade,
    ),
    SQLTask(
        task_id="hard_003",
        difficulty="hard",
        broken_query=(
            "SELECT dept, AVG(salary) AS avg_sal, MAX(salary) AS max_sal "
            "FORM employees "
            "WHER hire_date BETWEN '2020-01-01' AND '2023-12-31' AND status = 'active' "
            "GRUP BY dept "
            "HAVNG AVG(salary) > 60000 "
            "ORDR BY avg_sal DSC"
        ),
        canonical_answer=(
            "SELECT dept, AVG(salary) AS avg_sal, MAX(salary) AS max_sal "
            "FROM employees "
            "WHERE hire_date BETWEEN '2020-01-01' AND '2023-12-31' AND status = 'active' "
            "GROUP BY dept "
            "HAVING AVG(salary) > 60000 "
            "ORDER BY avg_sal DESC"
        ),
        schema_context=(
            "employees(id INT, name VARCHAR, dept VARCHAR, salary DECIMAL, "
            "hire_date DATE, status VARCHAR)"
        ),
        error_hint=None,
        max_steps=4,
        grader=grade,
    ),
    SQLTask(
        task_id="hard_004",
        difficulty="hard",
        broken_query=(
            "SELCT p.name, cat.category_name, SUM(oi.quantity) AS total_sold "
            "FORM products p "
            "INNE JOIN categories cat ON p.cat_id = cat.id "
            "INNE JOIN order_items oi ON p.id = oi.prod_id "
            "INNE JOIN orders o ON oi.order_id = o.id "
            "WHER o.status = 'completed' AND o.order_date >= '2024-01-01' "
            "GRUP BY p.name, cat.category_name "
            "ORDR BY total_sold DSC LIMT 20"
        ),
        canonical_answer=(
            "SELECT p.name, cat.category_name, SUM(oi.quantity) AS total_sold "
            "FROM products p "
            "INNER JOIN categories cat ON p.category_id = cat.id "
            "INNER JOIN order_items oi ON p.id = oi.product_id "
            "INNER JOIN orders o ON oi.order_id = o.id "
            "WHERE o.status = 'completed' AND o.order_date >= '2024-01-01' "
            "GROUP BY p.name, cat.category_name "
            "ORDER BY total_sold DESC LIMIT 20"
        ),
        schema_context=(
            "products(id INT, name VARCHAR, category_id INT, price DECIMAL)\n"
            "categories(id INT, category_name VARCHAR)\n"
            "order_items(id INT, order_id INT, product_id INT, quantity INT)\n"
            "orders(id INT, status VARCHAR, order_date DATE)"
        ),
        error_hint=None,
        max_steps=4,
        grader=grade,
    ),
    SQLTask(
        task_id="hard_005",
        difficulty="hard",
        broken_query=(
            "SELECT a.title, u.username, COUNT(c.id) AS comment_count, "
            "AVG(r.score) AS avg_score "
            "FORM articles a "
            "INNE JOIN users u ON a.author_id = u.id "
            "LFT JOIN comments c ON a.id = c.article_id "
            "LFT JOIN ratings r ON a.id = r.article_id "
            "WHER a.published_at BETWEN '2024-01-01' AND '2024-06-30' "
            "GRUP BY a.title, u.username "
            "HAVNG COUNT(c.id) > 5 "
            "ORDR BY avg_score DSC"
        ),
        canonical_answer=(
            "SELECT a.title, u.username, COUNT(c.id) AS comment_count, "
            "AVG(r.score) AS avg_score "
            "FROM articles a "
            "INNER JOIN users u ON a.author_id = u.id "
            "LEFT JOIN comments c ON a.id = c.article_id "
            "LEFT JOIN ratings r ON a.id = r.article_id "
            "WHERE a.published_at BETWEEN '2024-01-01' AND '2024-06-30' "
            "GROUP BY a.title, u.username "
            "HAVING COUNT(c.id) > 5 "
            "ORDER BY avg_score DESC"
        ),
        schema_context=(
            "articles(id INT, title VARCHAR, author_id INT, published_at DATE)\n"
            "users(id INT, username VARCHAR, email VARCHAR)\n"
            "comments(id INT, article_id INT, user_id INT, body TEXT)\n"
            "ratings(id INT, article_id INT, user_id INT, score FLOAT)"
        ),
        error_hint=None,
        max_steps=4,
        grader=grade,
    ),
    SQLTask(
        task_id="hard_006",
        difficulty="hard",
        broken_query=(
            "SELCT w.warehouse_name, p.name, SUM(inv.qty) AS stock_total "
            "FORM warehouses w "
            "INNE JOIN inventory inv ON w.id = inv.wrhs_id "
            "INNE JOIN products p ON inv.product_id = p.id "
            "WHER inv.last_updated >= '2024-01-01' "
            "GRUP BY w.warehouse_name, p.name "
            "HAVNG SUM(inv.qty) < 50 "
            "ORDR BY stock_total ASC"
        ),
        canonical_answer=(
            "SELECT w.warehouse_name, p.name, SUM(inv.qty) AS stock_total "
            "FROM warehouses w "
            "INNER JOIN inventory inv ON w.id = inv.warehouse_id "
            "INNER JOIN products p ON inv.product_id = p.id "
            "WHERE inv.last_updated >= '2024-01-01' "
            "GROUP BY w.warehouse_name, p.name "
            "HAVING SUM(inv.qty) < 50 "
            "ORDER BY stock_total ASC"
        ),
        schema_context=(
            "warehouses(id INT, warehouse_name VARCHAR, location VARCHAR)\n"
            "inventory(id INT, warehouse_id INT, product_id INT, qty INT, "
            "last_updated DATE)\n"
            "products(id INT, name VARCHAR, sku VARCHAR, price DECIMAL)"
        ),
        error_hint=None,
        max_steps=4,
        grader=grade,
    ),
    SQLTask(
        task_id="hard_007",
        difficulty="hard",
        broken_query=(
            "SELECT s.student_name, co.course_name, "
            "AVG(g.grade) AS avg_grade, COUNT(g.id) AS assignments_done "
            "FORM students s "
            "INNE JOIN enrollments en ON s.id = en.student_id "
            "INNE JOIN courses co ON en.course_id = co.id "
            "INNE JOIN grades g ON s.id = g.std_id AND co.id = g.course_id "
            "WHER en.semester = 'Fall2024' "
            "GRUP BY s.student_name, co.course_name "
            "HAVNG AVG(g.grade) >= 70 "
            "ORDR BY avg_grade DSC"
        ),
        canonical_answer=(
            "SELECT s.student_name, co.course_name, "
            "AVG(g.grade) AS avg_grade, COUNT(g.id) AS assignments_done "
            "FROM students s "
            "INNER JOIN enrollments en ON s.id = en.student_id "
            "INNER JOIN courses co ON en.course_id = co.id "
            "INNER JOIN grades g ON s.id = g.student_id AND co.id = g.course_id "
            "WHERE en.semester = 'Fall2024' "
            "GROUP BY s.student_name, co.course_name "
            "HAVING AVG(g.grade) >= 70 "
            "ORDER BY avg_grade DESC"
        ),
        schema_context=(
            "students(id INT, student_name VARCHAR, email VARCHAR)\n"
            "enrollments(id INT, student_id INT, course_id INT, semester VARCHAR)\n"
            "courses(id INT, course_name VARCHAR, credits INT)\n"
            "grades(id INT, student_id INT, course_id INT, grade FLOAT)"
        ),
        error_hint=None,
        max_steps=4,
        grader=grade,
    ),
    SQLTask(
        task_id="hard_008",
        difficulty="hard",
        broken_query=(
            "SELCT e.name, m.name AS manager_name, d.dept_name, "
            "e.salary, AVG(e2.salary) AS dept_avg "
            "FORM employees e "
            "LFT JOIN employees m ON e.manager_id = m.id "
            "INNE JOIN departments d ON e.dept_id = d.id "
            "INNE JOIN employees e2 ON e2.dept_id = e.dept_id "
            "WHER e.salary > 50000 "
            "GRUP BY e.name, m.name, d.dept_name, e.salary "
            "HAVNG e.salary > AVG(e2.salary) "
            "ORDR BY e.salary DSC"
        ),
        canonical_answer=(
            "SELECT e.name, m.name AS manager_name, d.dept_name, "
            "e.salary, AVG(e2.salary) AS dept_avg "
            "FROM employees e "
            "LEFT JOIN employees m ON e.manager_id = m.id "
            "INNER JOIN departments d ON e.dept_id = d.id "
            "INNER JOIN employees e2 ON e2.dept_id = e.dept_id "
            "WHERE e.salary > 50000 "
            "GROUP BY e.name, m.name, d.dept_name, e.salary "
            "HAVING e.salary > AVG(e2.salary) "
            "ORDER BY e.salary DESC"
        ),
        schema_context=(
            "employees(id INT, name VARCHAR, dept_id INT, manager_id INT, "
            "salary DECIMAL)\n"
            "departments(id INT, dept_name VARCHAR, budget DECIMAL)"
        ),
        error_hint=None,
        max_steps=4,
        grader=grade,
    ),
    SQLTask(
        task_id="hard_009",
        difficulty="hard",
        broken_query=(
            "SELECT t.tag_name, COUNT(DISTINCT pt.post_id) AS post_count, "
            "AVG(p.views) AS avg_views "
            "FORM tags t "
            "INNE JOIN post_tags pt ON t.id = pt.tag_id "
            "INNE JOIN posts p ON pt.post_id = p.id "
            "INNE JOIN users u ON p.user_id = u.id "
            "WHER p.created_at >= '2024-01-01' AND u.role = 'author' "
            "GRUP BY t.tag_name "
            "HAVNG COUNT(DISTINCT pt.post_id) > 10 "
            "ORDR BY avg_views DSC LIMT 15"
        ),
        canonical_answer=(
            "SELECT t.tag_name, COUNT(DISTINCT pt.post_id) AS post_count, "
            "AVG(p.views) AS avg_views "
            "FROM tags t "
            "INNER JOIN post_tags pt ON t.id = pt.tag_id "
            "INNER JOIN posts p ON pt.post_id = p.id "
            "INNER JOIN users u ON p.user_id = u.id "
            "WHERE p.created_at >= '2024-01-01' AND u.role = 'author' "
            "GROUP BY t.tag_name "
            "HAVING COUNT(DISTINCT pt.post_id) > 10 "
            "ORDER BY avg_views DESC LIMIT 15"
        ),
        schema_context=(
            "tags(id INT, tag_name VARCHAR)\n"
            "post_tags(post_id INT, tag_id INT)\n"
            "posts(id INT, user_id INT, title VARCHAR, views INT, "
            "created_at DATE)\n"
            "users(id INT, username VARCHAR, role VARCHAR)"
        ),
        error_hint=None,
        max_steps=4,
        grader=grade,
    ),
    SQLTask(
        task_id="hard_010",
        difficulty="hard",
        broken_query=(
            "SELCT proj.name AS project_name, emp.name AS employee_name, "
            "SUM(ts.hours) AS total_hours, ts.week_start "
            "FORM projects proj "
            "INNE JOIN project_members pm ON proj.id = pm.proj_id "
            "INNE JOIN employees emp ON pm.employee_id = emp.id "
            "INNE JOIN timesheets ts ON emp.id = ts.emp_id "
            "AND proj.id = ts.project_id "
            "WHER ts.week_start BETWEN '2024-01-01' AND '2024-03-31' "
            "AND proj.status = 'active' "
            "GRUP BY proj.name, emp.name, ts.week_start "
            "HAVNG SUM(ts.hours) > 40 "
            "ORDR BY total_hours DSC"
        ),
        canonical_answer=(
            "SELECT proj.name AS project_name, emp.name AS employee_name, "
            "SUM(ts.hours) AS total_hours, ts.week_start "
            "FROM projects proj "
            "INNER JOIN project_members pm ON proj.id = pm.project_id "
            "INNER JOIN employees emp ON pm.employee_id = emp.id "
            "INNER JOIN timesheets ts ON emp.id = ts.employee_id "
            "AND proj.id = ts.project_id "
            "WHERE ts.week_start BETWEEN '2024-01-01' AND '2024-03-31' "
            "AND proj.status = 'active' "
            "GROUP BY proj.name, emp.name, ts.week_start "
            "HAVING SUM(ts.hours) > 40 "
            "ORDER BY total_hours DESC"
        ),
        schema_context=(
            "projects(id INT, name VARCHAR, status VARCHAR, budget DECIMAL)\n"
            "project_members(id INT, project_id INT, employee_id INT, role VARCHAR)\n"
            "employees(id INT, name VARCHAR, dept_id INT, hourly_rate DECIMAL)\n"
            "timesheets(id INT, employee_id INT, project_id INT, "
            "hours DECIMAL, week_start DATE)"
        ),
        error_hint=None,
        max_steps=4,
        grader=grade,
    ),
]
