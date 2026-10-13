import io
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import main

GOOD_ARGS = [
    "--package", "org.example:app",
    "--repo", "https://repo1.maven.org/maven2",
    "--output", "graph.svg",
    "--filter", "test",
]


def run_main(args):
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main.main(args)
    return code, out.getvalue(), err.getvalue()


class TestGoodParams(unittest.TestCase):

    def test_print_all_params(self):
        """Все параметры выводятся в формате ключ-значение"""
        code, out, _ = run_main(GOOD_ARGS)
        self.assertEqual(code, 0)
        self.assertIn("package = org.example:app", out)
        self.assertIn("repo = https://repo1.maven.org/maven2", out)
        self.assertIn("mode = real", out)
        self.assertIn("output = graph.svg", out)
        self.assertIn("filter = test", out)

    def test_test_mode_with_file(self):
        """В тестовом режиме принимается существующий файл"""
        args = ["--package", "A", "--repo", __file__,
                "--mode", "test", "--output", "graph.svg"]
        code, out, _ = run_main(args)
        self.assertEqual(code, 0)
        self.assertIn("mode = test", out)
        self.assertIn("filter = None", out)


class TestBadParams(unittest.TestCase):

    def check_error(self, args, text):
        """Проверить, что программа сообщает об ошибке"""
        code, out, err = run_main(args)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn(text, err)

    def test_no_package(self):
        """Не задано имя пакета"""
        args = ["--repo", "https://x.org", "--output", "g.svg"]
        self.check_error(args, "не задано имя пакета")

    def test_package_with_space(self):
        """Имя пакета содержит пробел"""
        args = ["--package", "a b", "--repo", "https://x.org",
                "--output", "g.svg"]
        self.check_error(args, "пробелы")

    def test_no_repo(self):
        """Не задан репозиторий"""
        args = ["--package", "A", "--output", "g.svg"]
        self.check_error(args, "не задан репозиторий")

    def test_bad_url(self):
        """URL не начинается с http:// или https://"""
        args = ["--package", "A", "--repo", "ftp://x.org",
                "--output", "g.svg"]
        self.check_error(args, "URL репозитория")

    def test_missing_test_file(self):
        """Файл тестового репозитория не существует"""
        args = ["--package", "A", "--repo", "no_such_file.txt",
                "--mode", "test", "--output", "g.svg"]
        self.check_error(args, "не найден")

    def test_bad_mode(self):
        """Неизвестный режим работы"""
        args = ["--package", "A", "--repo", "https://x.org",
                "--mode", "abc", "--output", "g.svg"]
        self.check_error(args, "режим")

    def test_no_output(self):
        """Не задано имя файла изображения"""
        args = ["--package", "A", "--repo", "https://x.org"]
        self.check_error(args, "не задано имя файла")

    def test_bad_output_extension(self):
        """Имя файла изображения без расширения .svg"""
        args = ["--package", "A", "--repo", "https://x.org",
                "--output", "g.png"]
        self.check_error(args, ".svg")

    def test_empty_filter(self):
        """Подстрока фильтра пустая"""
        args = ["--package", "A", "--repo", "https://x.org",
                "--output", "g.svg", "--filter", " "]
        self.check_error(args, "фильтр")


if __name__ == "__main__":
    unittest.main()
