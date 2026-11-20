import logging
import re

import sqlparse
from sqlparse import tokens as T

from model import DatabaseModel, FormatterModel, MAX_ROWS

logger = logging.getLogger("mvvm_app")

MAX_QUERY_CHARS = 10_000
MAX_INPUT_CHARS = 500_000
IDENTIFIER = re.compile(r"^[A-Za-z0-9_]{1,64}$")
READ_START = {"SELECT", "SHOW", "DESCRIBE", "DESC", "EXPLAIN"}
FORBIDDEN = {"INTO", "FOR", "LOCK", "SET", "INSERT", "UPDATE", "DELETE", "DROP",
             "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE", "CALL", "LOAD",
             "RENAME", "COMMIT", "ROLLBACK", "START"}


def validate_read_only(query):
    if not query.strip():
        raise ValueError("La requête est vide.")
    if len(query) > MAX_QUERY_CHARS:
        raise ValueError("La requête est trop longue.")
    statements = [s for s in sqlparse.parse(query) if str(s).strip(" \t\r\n;")]
    if len(statements) != 1:
        raise ValueError("Une seule instruction est autorisée.")
    stmt = statements[0]
    first = stmt.token_first(skip_cm=True)
    if first is None or first.normalized.upper() not in READ_START:
        raise ValueError("Seules les requêtes de lecture (SELECT, SHOW...) sont autorisées.")
    for token in stmt.flatten():
        if token.ttype in T.Keyword and token.normalized.upper() in FORBIDDEN:
            raise ValueError(f"Mot-clé interdit : {token.normalized.upper()}")


def build_preview_query(table):
    table = table.strip()
    if not IDENTIFIER.match(table):
        raise ValueError("Nom de table invalide (lettres, chiffres et _ uniquement).")
    return f"SELECT * FROM `{table}` LIMIT 100"


def format_table(columns, rows, truncated=False):
    if not columns:
        return "Aucun résultat."
    lines = [" | ".join(columns), "-" * 40]
    for row in rows:
        lines.append(" | ".join("" if v is None else str(v) for v in row))
    if truncated:
        lines.append(f"\n(Résultats tronqués à {MAX_ROWS} lignes.)")
    return "\n".join(lines)


class NoteViewModel:
    def __init__(self, on_close):
        self._on_close = on_close

    def close(self):
        self._on_close(self)


class DatabaseViewModel:
    def __init__(self):
        self.output = ""

    def run(self, ip, port, user, password, database, query, use_tls=False):
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            self.output = "Port invalide."
            return self.output
        try:
            validate_read_only(query)
        except ValueError as e:
            self.output = str(e)
            return self.output
        try:
            columns, rows, truncated = DatabaseModel.fetch(
                ip, port, user, password, database, query, use_tls)
            self.output = format_table(columns, rows, truncated)
        except Exception:
            logger.exception("Échec de la requête SQL sur %s:%s", ip, port)
            self.output = "Erreur lors de l'exécution. Détails dans mvvm_app.log."
        return self.output


class FormatViewModel:
    def __init__(self):
        self.output = ""

    def format(self, language, text):
        if len(text) > MAX_INPUT_CHARS:
            self.output = "Texte trop volumineux (500 000 caractères maximum)."
            return
        try:
            self.output = FormatterModel.format(language, text)
        except Exception as e:
            self.output = f"Texte invalide pour {language} : {e}"


class MainViewModel:
    def __init__(self):
        self.notes = []

    def add_note(self):
        note = NoteViewModel(self.remove_note)
        self.notes.append(note)
        return note

    def remove_note(self, note):
        if note in self.notes:
            self.notes.remove(note)
