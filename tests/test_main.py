import io
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import main

GOOD_ARGS = [
    "--package", "junit:junit:4.13.2",
    "--repo", "https://repo1.maven.org/maven2",
    "--output", "graph.svg",
]

POM_TEXT = """<project>
  <dependencies>
    <dependency>
      <groupId>org.hamcrest</groupId>
      <artifactId>hamcrest-core</artifactId>
      <version>1.3</version>
    </dependency>
  </dependencies>
</project>
"""

def run_main(args):
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main.main(args)
    return code, out.getvalue(), err.getvalue()


class TestDependencies(unittest.TestCase):

    def test_print_dependencies(self):
        """Выводятся все прямые зависимости пакета."""
        with mock.patch("maven.download_text", return_value=POM_TEXT):
            code, out, _ = run_main(GOOD_ARGS)
        self.assertEqual(code, 0)
        self.assertIn("Прямые зависимости пакета junit:junit:4.13.2:", out)
        self.assertIn("org.hamcrest:hamcrest-core:1.3", out)

    def test_no_dependencies(self):
        """Сообщение, если у пакета нет зависимостей."""
        with mock.patch("maven.download_text", return_value="<project/>"):
            code, out, _ = run_main(GOOD_ARGS)
        self.assertEqual(code, 0)
        self.assertIn("нет зависимостей", out)

    def test_download_error(self):
        """Ошибка загрузки выводится как ошибка программы."""
        error = ValueError("не удалось загрузить файл")
        with mock.patch("maven.download_text", side_effect=error):
            code, out, err = run_main(GOOD_ARGS)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("не удалось загрузить", err)


class TestBadParams(unittest.TestCase):

    def check_error(self, args, text):
        code, out, err = run_main(args)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn(text, err)

    def test_no_package(self):
        """Не задано имя пакета."""
        args = ["--repo", "https://x.org", "--output", "g.svg"]
        self.check_error(args, "не задано имя пакета")

    def test_package_with_space(self):
        """Имя пакета содержит пробел."""
        args = ["--package", "a b", "--repo", "https://x.org",
                "--output", "g.svg"]
        self.check_error(args, "пробелы")

    def test_package_without_version(self):
        """Имя пакета без версии."""
        args = ["--package", "junit:junit", "--repo", "https://x.org",
                "--output", "g.svg"]
        self.check_error(args, "groupId:artifactId:version")

    def test_package_with_empty_part(self):
        """Имя пакета с пустой частью."""
        args = ["--package", "junit::4.13.2", "--repo", "https://x.org",
                "--output", "g.svg"]
        self.check_error(args, "groupId:artifactId:version")

    def test_no_repo(self):
        """Не задан репозиторий."""
        args = ["--package", "a:b:1", "--output", "g.svg"]
        self.check_error(args, "не задан репозиторий")

    def test_bad_url(self):
        """URL не начинается с http:// или https://."""
        args = ["--package", "a:b:1", "--repo", "ftp://x.org",
                "--output", "g.svg"]
        self.check_error(args, "URL репозитория")

    def test_missing_test_file(self):
        """Файл тестового репозитория не существует."""
        args = ["--package", "A", "--repo", "no_such_file.txt",
                "--mode", "test", "--output", "g.svg"]
        self.check_error(args, "не найден")

    def test_test_mode_not_supported(self):
        """Режим test пока не поддерживается."""
        args = ["--package", "A", "--repo", __file__,
                "--mode", "test", "--output", "g.svg"]
        self.check_error(args, "пока не поддерживается")

    def test_bad_mode(self):
        """Неизвестный режим работы."""
        args = ["--package", "a:b:1", "--repo", "https://x.org",
                "--mode", "abc", "--output", "g.svg"]
        self.check_error(args, "режим")

    def test_no_output(self):
        """Не задано имя файла изображения."""
        args = ["--package", "a:b:1", "--repo", "https://x.org"]
        self.check_error(args, "не задано имя файла")

    def test_bad_output_extension(self):
        """Имя файла изображения без расширения .svg."""
        args = ["--package", "a:b:1", "--repo", "https://x.org",
                "--output", "g.png"]
        self.check_error(args, ".svg")

    def test_empty_filter(self):
        """Подстрока фильтра пустая."""
        args = ["--package", "a:b:1", "--repo", "https://x.org",
                "--output", "g.svg", "--filter", " "]
        self.check_error(args, "фильтр")


if __name__ == "__main__":
    unittest.main()