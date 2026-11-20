import json

import defusedxml.minidom
import pymysql
import sqlparse

MAX_ROWS = 1000
TIMEOUT = 10


class DatabaseModel:
    @staticmethod
    def fetch(ip, port, user, password, database, query, use_tls=False):
        kwargs = dict(host=ip, port=int(port), user=user, password=password,
                      database=database or None, charset="utf8mb4",
                      connect_timeout=TIMEOUT, read_timeout=TIMEOUT,
                      write_timeout=TIMEOUT)
        if use_tls:
            kwargs["ssl"] = {"check_hostname": True}
        conn = pymysql.connect(**kwargs)
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                columns = [d[0] for d in cur.description or []]
                rows = cur.fetchmany(MAX_ROWS + 1)
                return columns, rows[:MAX_ROWS], len(rows) > MAX_ROWS
        finally:
            conn.close()


class FormatterModel:
    LANGUAGES = ("JSON", "XML", "SQL", "Python")

    @staticmethod
    def format(language, text):
        if language == "JSON":
            return json.dumps(json.loads(text), indent=4, ensure_ascii=False)
        if language == "XML":
            pretty = defusedxml.minidom.parseString(text).toprettyxml(indent="    ")
            return "\n".join(line for line in pretty.splitlines() if line.strip())
        if language == "SQL":
            return sqlparse.format(text, reindent=True, keyword_case="upper")
        if language == "Python":
            import black
            return black.format_str(text, mode=black.Mode())
        raise ValueError(f"Langage non supporté : {language}")
