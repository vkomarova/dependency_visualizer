import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "", "src"))

import repo_file

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class TestParseTestRepo(unittest.TestCase):

    def test_parse(self):
        """Строки разбираются в словарь пакетов и зависимостей."""
        text = "A: B C\n\nB: C\nC:\n"
        result = repo_file.parse_test_repo(text)
        self.assertEqual(result, {"A": ["B", "C"], "B": ["C"], "C": []})

    def test_no_colon(self):
        """Строка без двоеточия вызывает ошибку с номером строки."""
        with self.assertRaises(ValueError) as context:
            repo_file.parse_test_repo("A: B\nB C\n")
        self.assertIn("строка 2", str(context.exception))

    def test_small_letters(self):
        """Имя пакета из маленьких букв вызывает ошибку."""
        with self.assertRaises(ValueError):
            repo_file.parse_test_repo("a: B\n")

    def test_bad_dependency_name(self):
        """Имя зависимости не из латинских букв вызывает ошибку."""
        with self.assertRaises(ValueError):
            repo_file.parse_test_repo("A: B1\n")

    def test_is_test_name(self):
        """Подходят только большие латинские буквы."""
        self.assertTrue(repo_file.is_test_name("A"))
        self.assertTrue(repo_file.is_test_name("AB"))
        self.assertFalse(repo_file.is_test_name("a"))
        self.assertFalse(repo_file.is_test_name("А"))
        self.assertFalse(repo_file.is_test_name("A1"))

    def test_get_test_dependencies(self):
        """У пакета, которого нет в файле, нет зависимостей."""
        repo = {"A": ["B"]}
        self.assertEqual(repo_file.get_test_dependencies(repo, "A"), ["B"])
        self.assertEqual(repo_file.get_test_dependencies(repo, "B"), [])


class TestLoadTestRepo(unittest.TestCase):

    def test_load_file(self):
        """Файл из папки data читается правильно."""
        path = os.path.join(DATA_DIR, "cycle.txt")
        result = repo_file.load_test_repo(path)
        self.assertEqual(result["C"], ["A", "D"])

    def test_missing_file(self):
        """Отсутствующий файл вызывает ошибку."""
        with self.assertRaises(ValueError):
            repo_file.load_test_repo("no_such_file.txt")


if __name__ == "__main__":
    unittest.main()