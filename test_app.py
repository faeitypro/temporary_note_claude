import unittest

from viewmodel import validate_read_only, build_preview_query, FormatViewModel


class TestReadOnly(unittest.TestCase):
    def test_select_accepted(self):
        validate_read_only("SELECT id FROM users WHERE id = 1")

    def test_show_accepted(self):
        validate_read_only("SHOW TABLES")

    def test_write_refused(self):
        with self.assertRaises(ValueError):
            validate_read_only("DELETE FROM users")

    def test_into_outfile_refused(self):
        with self.assertRaises(ValueError):
            validate_read_only("SELECT * FROM users INTO OUTFILE '/tmp/x'")

    def test_for_update_refused(self):
        with self.assertRaises(ValueError):
            validate_read_only("SELECT * FROM users FOR UPDATE")

    def test_multiple_statements_refused(self):
        with self.assertRaises(ValueError):
            validate_read_only("SELECT 1; DROP TABLE users")


class TestPreview(unittest.TestCase):
    def test_valid_table(self):
        self.assertEqual(build_preview_query("users"),
                         "SELECT * FROM `users` LIMIT 100")

    def test_invalid_table(self):
        with self.assertRaises(ValueError):
            build_preview_query("users; DROP TABLE x")


class TestFormat(unittest.TestCase):
    def test_json(self):
        vm = FormatViewModel()
        vm.format("JSON", '{"a":1}')
        self.assertIn('"a": 1', vm.output)


if __name__ == "__main__":
    unittest.main()
