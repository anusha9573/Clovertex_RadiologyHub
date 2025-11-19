# services/api/app/db/repositories.py
from datetime import datetime

from services.api.app.config import DB_DIALECT
from services.api.app.db.mysql import get_connection

PLACEHOLDER = "%s" if DB_DIALECT == "mysql" else "?"


def _adapt_sql(sql: str) -> str:
    if DB_DIALECT == "mysql":
        return sql
    return sql.replace("%s", "?")


def _placeholders(count: int) -> str:
    return ",".join([PLACEHOLDER] * count)


def _cursor(conn, dictionary: bool = False):
    if DB_DIALECT == "mysql":
        return conn.cursor(dictionary=dictionary)
    return conn.cursor()


def _rows_to_dicts(rows):
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, dict):
        return rows
    return [dict(r) for r in rows]


def _row_to_dict(row):
    if row is None or isinstance(row, dict):
        return row
    return dict(row)


def _as_db_datetime(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return value


class ResourcesRepo:
    @staticmethod
    def list_resources():
        conn = get_connection()
        cur = _cursor(conn, dictionary=True)
        cur.execute(
            "SELECT resource_id, name, specialty, skill_level, total_cases_handled FROM resources"
        )
        rows = cur.fetchall()
        rows = _rows_to_dicts(rows)
        cur.close()
        conn.close()
        return rows

    @staticmethod
    def get_by_specialty(specialties):
        if not specialties:
            return []
        specialties = [s for s in specialties if s]
        if not specialties:
            return []
        conn = get_connection()
        cur = _cursor(conn, dictionary=True)
        placeholders = _placeholders(len(specialties))
        sql = f"""SELECT resource_id, name, specialty, skill_level, total_cases_handled
                  FROM resources WHERE specialty IN ({placeholders})"""
        cur.execute(sql, specialties)
        rows = cur.fetchall()
        rows = _rows_to_dicts(rows)
        cur.close()
        conn.close()
        return rows

    @staticmethod
    def get_by_ids(ids_list):
        if not ids_list:
            return []
        conn = get_connection()
        cur = _cursor(conn, dictionary=True)
        placeholders = _placeholders(len(ids_list))
        sql = f"""SELECT resource_id, name, specialty, skill_level, total_cases_handled
                  FROM resources WHERE resource_id IN ({placeholders})"""
        cur.execute(sql, ids_list)
        rows = cur.fetchall()
        rows = _rows_to_dicts(rows)
        cur.close()
        conn.close()
        return rows

    @staticmethod
    def increment_cases_handled(resource_id, delta=1):
        conn = get_connection()
        cur = _cursor(conn)
        sql = _adapt_sql(
            "UPDATE resources SET total_cases_handled = COALESCE(total_cases_handled,0) + %s WHERE resource_id=%s"
        )
        cur.execute(
            sql,
            (delta, resource_id),
        )
        conn.commit()
        cur.close()
        conn.close()


class ResourceCalendarRepo:
    @staticmethod
    def get_calendars_for_resources_on_date(resource_ids, date_str):
        if not resource_ids:
            return {}
        conn = get_connection()
        cur = _cursor(conn, dictionary=True)
        placeholders = _placeholders(len(resource_ids))
        sql = f"""SELECT resource_id, calendar_id, date, available_from, available_to, current_workload
                  FROM resource_calendar
                  WHERE resource_id IN ({placeholders}) AND date={PLACEHOLDER}
                  ORDER BY available_from"""
        params = tuple(resource_ids) + (date_str,)
        cur.execute(sql, params)
        rows = cur.fetchall()
        rows = _rows_to_dicts(rows)
        cur.close()
        conn.close()
        mapping = {}
        for row in rows:
            mapping.setdefault(row["resource_id"], []).append(row)
        return mapping

    @staticmethod
    def increment_workload(calendar_id, delta=1):
        conn = get_connection()
        cur = _cursor(conn)
        sql = _adapt_sql(
            "UPDATE resource_calendar SET current_workload = COALESCE(current_workload,0) + %s WHERE calendar_id=%s"
        )
        cur.execute(
            sql,
            (delta, calendar_id),
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def get_on_duty(date_str):
        """
        Return combined calendar + resource profile rows for a specific date.
        """
        conn = get_connection()
        cur = _cursor(conn, dictionary=True)
        sql = _adapt_sql(
            """SELECT rc.calendar_id, rc.resource_id, rc.date, rc.available_from,
                      rc.available_to, rc.current_workload,
                      r.name, r.specialty, r.skill_level, r.total_cases_handled
               FROM resource_calendar rc
               INNER JOIN resources r ON rc.resource_id = r.resource_id
               WHERE rc.date=%s
               ORDER BY rc.available_from"""
        )
        cur.execute(sql, (date_str,))
        rows = cur.fetchall()
        rows = _rows_to_dicts(rows)
        cur.close()
        conn.close()
        return rows


class SpecialtyMappingRepo:
    @staticmethod
    def get_by_work_type(work_type):
        conn = get_connection()
        cur = _cursor(conn, dictionary=True)
        sql = _adapt_sql(
            "SELECT work_type, required_specialty, alternate_specialty FROM specialty_mapping WHERE work_type=%s"
        )
        cur.execute(sql, (work_type,))
        row = cur.fetchone()
        row = _row_to_dict(row)
        cur.close()
        conn.close()
        return row


class WorkRequestsRepo:
    @staticmethod
    def create_work_request(record: dict):
        conn = get_connection()
        cur = _cursor(conn)
        sql = _adapt_sql(
            """INSERT INTO work_requests
                 (work_id, work_type, description, priority, scheduled_timestamp, status, assigned_to)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)"""
        )
        cur.execute(
            sql,
            (
                record["work_id"],
                record["work_type"],
                record["description"],
                record["priority"],
                _as_db_datetime(record["scheduled_timestamp"]),
                record.get("status", "pending"),
                record.get("assigned_to"),
            ),
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def get_work_by_id(work_id):
        conn = get_connection()
        cur = _cursor(conn, dictionary=True)
        sql = _adapt_sql(
            """SELECT work_id, work_type, description, priority,
                      scheduled_timestamp, status, assigned_to
               FROM work_requests WHERE work_id=%s"""
        )
        cur.execute(sql, (work_id,))
        row = cur.fetchone()
        row = _row_to_dict(row)
        cur.close()
        conn.close()
        return row

    @staticmethod
    def assign_work(work_id, resource_id):
        conn = get_connection()
        cur = _cursor(conn)
        sql = _adapt_sql(
            "UPDATE work_requests SET assigned_to=%s, status=%s WHERE work_id=%s"
        )
        cur.execute(
            sql,
            (resource_id, "assigned", work_id),
        )
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def list_work_requests(limit=50, status=None):
        conn = get_connection()
        cur = _cursor(conn, dictionary=True)
        params = []
        sql = """SELECT work_id, work_type, description, priority,
                        scheduled_timestamp, status, assigned_to
                 FROM work_requests"""
        if status:
            sql += " WHERE status=%s"
            params.append(status)
        sql += " ORDER BY scheduled_timestamp DESC LIMIT %s"
        params.append(int(limit))
        sql = _adapt_sql(sql)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        rows = _rows_to_dicts(rows)
        cur.close()
        conn.close()
        return rows
