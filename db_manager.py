import sqlite3
from datetime import datetime
import os

class DBManager:
    def __init__(self, db_path="data/applications.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database and create the applications table if it doesn't exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT,
                    job_title TEXT,
                    company TEXT,
                    location TEXT,
                    url TEXT,
                    ats_score INTEGER,
                    ats_reason TEXT,
                    status TEXT,
                    date_applied TEXT,
                    tailored_resume_used BOOLEAN
                )
            ''')
            conn.commit()

    def log_application(self, job_id, job_title, company, location, url, ats_score=None, ats_reason=None, status="Applied", tailored=False):
        """Logs a job application attempt to the database."""
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO applications 
                (job_id, job_title, company, location, url, ats_score, ats_reason, status, date_applied, tailored_resume_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job_id, job_title, company, location, url, ats_score, ats_reason, status, date_now, tailored))
            conn.commit()

    def get_all_applications(self):
        """Returns all logged applications."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM applications ORDER BY date_applied DESC')
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self):
        """Returns basic statistics about applications."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status, COUNT(*) FROM applications GROUP BY status')
            return dict(cursor.fetchall())