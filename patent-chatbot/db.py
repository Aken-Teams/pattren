"""
MySQL Database Module for PatentAI
"""

import pymysql
from contextlib import contextmanager

DB_CONFIG = {
    "host": "122.100.99.161",
    "port": 43306,
    "user": "A999",
    "password": "1023",
    "database": "db_A999",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "connect_timeout": 10,
}


@contextmanager
def get_db():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ═══════════════════════════════════════════
# Dashboard Stats
# ═══════════════════════════════════════════

def get_dashboard_stats():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COALESCE(SUM(patent_count), 0) AS total_patents FROM pat_projects")
        total_patents = c.fetchone()["total_patents"]

        c.execute("SELECT COUNT(*) AS cnt FROM pat_projects WHERE status='active'")
        active_projects = c.fetchone()["cnt"]

        c.execute("SELECT COALESCE(SUM(risk_count), 0) AS total_risks FROM pat_projects WHERE risk_count > 0")
        total_risks = c.fetchone()["total_risks"]

        c.execute("SELECT COUNT(*) AS cnt FROM pat_search_history")
        search_count = c.fetchone()["cnt"]

        return {
            "total_patents": int(total_patents),
            "active_projects": int(active_projects),
            "total_risks": int(total_risks),
            "search_count": int(search_count),
        }


# ═══════════════════════════════════════════
# Projects
# ═══════════════════════════════════════════

def get_projects(status=None, limit=20):
    with get_db() as conn:
        c = conn.cursor()
        sql = "SELECT p.*, u.display_name as owner_name FROM pat_projects p LEFT JOIN pat_users u ON p.owner_id = u.id"
        if status:
            sql += " WHERE p.status = %s"
            sql += " ORDER BY p.updated_at DESC LIMIT %s"
            c.execute(sql, (status, limit))
        else:
            sql += " ORDER BY p.updated_at DESC LIMIT %s"
            c.execute(sql, (limit,))
        return c.fetchall()


def get_project(project_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT p.*, u.display_name as owner_name FROM pat_projects p LEFT JOIN pat_users u ON p.owner_id = u.id WHERE p.id = %s", (project_id,))
        project = c.fetchone()
        if project:
            c.execute("""SELECT u.id, u.display_name, u.avatar_initials, pm.role
                        FROM pat_project_members pm JOIN pat_users u ON pm.user_id = u.id
                        WHERE pm.project_id = %s""", (project_id,))
            project["members"] = c.fetchall()
        return project


def create_project(name, description="", owner_id=None):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO pat_projects (name, description, owner_id) VALUES (%s, %s, %s)",
                  (name, description, owner_id))
        project_id = c.lastrowid
        if owner_id:
            c.execute("INSERT INTO pat_project_members (project_id, user_id, role) VALUES (%s, %s, 'lead')",
                      (project_id, owner_id))
        return project_id


def update_project(project_id, **kwargs):
    with get_db() as conn:
        c = conn.cursor()
        fields = []
        values = []
        for k, v in kwargs.items():
            if k in ("name", "description", "status", "patent_count", "risk_count", "progress"):
                fields.append(f"{k} = %s")
                values.append(v)
        if fields:
            values.append(project_id)
            c.execute(f"UPDATE pat_projects SET {', '.join(fields)} WHERE id = %s", values)
            return True
    return False


# ═══════════════════════════════════════════
# Patents
# ═══════════════════════════════════════════

def save_patent(patent_data, project_id=None):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""INSERT INTO pat_patents (patent_number, title, abstract, applicant, inventors,
                    filing_date, publication_date, ipc_code, source, url, project_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE title=VALUES(title)""",
                  (patent_data.get("patent_number"), patent_data.get("title"),
                   patent_data.get("abstract"), patent_data.get("applicant"),
                   patent_data.get("inventors"), patent_data.get("filing_date"),
                   patent_data.get("publication_date"), patent_data.get("ipc_code"),
                   patent_data.get("source"), patent_data.get("url"), project_id))
        return c.lastrowid


def get_patents(project_id=None, limit=50):
    with get_db() as conn:
        c = conn.cursor()
        if project_id:
            c.execute("SELECT * FROM pat_patents WHERE project_id = %s ORDER BY created_at DESC LIMIT %s",
                      (project_id, limit))
        else:
            c.execute("SELECT * FROM pat_patents ORDER BY created_at DESC LIMIT %s", (limit,))
        return c.fetchall()


# ═══════════════════════════════════════════
# Search History
# ═══════════════════════════════════════════

def save_search(user_id, query, results_count=0, results_data=None):
    import json
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO pat_search_history (user_id, query, results_count, results_data) VALUES (%s, %s, %s, %s)",
                  (user_id, query, results_count, json.dumps(results_data) if results_data else None))
        return c.lastrowid


def get_search_history(user_id=None, limit=20):
    with get_db() as conn:
        c = conn.cursor()
        if user_id:
            c.execute("SELECT * FROM pat_search_history WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                      (user_id, limit))
        else:
            c.execute("SELECT * FROM pat_search_history ORDER BY created_at DESC LIMIT %s", (limit,))
        return c.fetchall()


# ═══════════════════════════════════════════
# Activity Log
# ═══════════════════════════════════════════

def log_activity(user_id, action_type, title, description="", related_project_id=None):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""INSERT INTO pat_activity_log (user_id, action_type, title, description, related_project_id)
                    VALUES (%s, %s, %s, %s, %s)""",
                  (user_id, action_type, title, description, related_project_id))
        return c.lastrowid


def get_activity_log(limit=20):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""SELECT a.*, u.display_name, u.avatar_initials
                    FROM pat_activity_log a LEFT JOIN pat_users u ON a.user_id = u.id
                    ORDER BY a.created_at DESC LIMIT %s""", (limit,))
        return c.fetchall()


# ═══════════════════════════════════════════
# Analysis
# ═══════════════════════════════════════════

def save_analysis(user_id, patent_a, patent_b, similarity_score, risk_level, ai_summary, claim_matrix=None):
    import json
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""INSERT INTO pat_analysis_records (user_id, patent_a, patent_b, similarity_score, risk_level, ai_summary, claim_matrix)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                  (user_id, patent_a, patent_b, similarity_score, risk_level, ai_summary,
                   json.dumps(claim_matrix) if claim_matrix else None))
        return c.lastrowid


# ═══════════════════════════════════════════
# Drafts
# ═══════════════════════════════════════════

def save_draft(user_id, title, tech_field, core_description, prior_art_issues="", reference_patents="", generated_content=""):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""INSERT INTO pat_draft_documents (user_id, title, tech_field, core_description, prior_art_issues, reference_patents, generated_content)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                  (user_id, title, tech_field, core_description, prior_art_issues, reference_patents, generated_content))
        return c.lastrowid


def get_drafts(user_id=None, limit=20):
    with get_db() as conn:
        c = conn.cursor()
        if user_id:
            c.execute("SELECT * FROM pat_draft_documents WHERE user_id = %s ORDER BY updated_at DESC LIMIT %s",
                      (user_id, limit))
        else:
            c.execute("SELECT * FROM pat_draft_documents ORDER BY updated_at DESC LIMIT %s", (limit,))
        return c.fetchall()


# ═══════════════════════════════════════════
# Users
# ═══════════════════════════════════════════

def get_users():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, display_name, email, avatar_initials, role FROM pat_users ORDER BY id")
        return c.fetchall()
