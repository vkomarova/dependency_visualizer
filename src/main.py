import argparse
import os
import sys

MODE_REAL = "real"
MODE_TEST = "test"
URL_PREFIXES = ("http://", "https://")
IMAGE_EXTENSION = ".svg"

def create_parser():
    parser = argparse.ArgumentParser(
        description="Визуализация графа зависимостей пакетов.")
    parser.add_argument("--package", help="имя анализируемого пакета")
    parser.add_argument(
        "--repo", help="URL репозитория или путь к файлу тестового репозитория")
    parser.add_argument("--mode", default=MODE_REAL,
        help="режим работы с репозиторием: real или test (по умолчанию real)")
    parser.add_argument("--output", help="имя файла с изображением графа (.svg)")
    parser.add_argument("--filter", help="подстрока для фильтрации пакетов")
    return parser

def check_package(package):
    if not package or not package.strip():
        raise ValueError("не задано имя пакета (--package)")
    if " " in package:
        raise ValueError("имя пакета не должно содержать пробелы")

def check_mode(mode):
    if mode not in (MODE_REAL, MODE_TEST):
        raise ValueError("режим (--mode) должен быть real или test")

def check_repo(repo, mode):
    if not repo or not repo.strip():
        raise ValueError("не задан репозиторий (--repo)")
    if mode == MODE_REAL and not repo.startswith(URL_PREFIXES):
        raise ValueError("URL репозитория должен начинаться с http:// или https://")
    if mode == MODE_TEST and not os.path.isfile(repo):
        raise ValueError("файл тестового репозитория не найден: " + repo)

def check_output(output):
    if not output or not output.strip():
        raise ValueError("не задано имя файла изображения (--output)")
    if not output.endswith(IMAGE_EXTENSION):
        raise ValueError("файл изображения должен иметь расширение .svg")

def check_filter(text):
    if text is not None and not text.strip():
        raise ValueError("подстрока фильтра (--filter) не может быть пустой")

def check_params(params):
    check_package(params.package)
    check_mode(params.mode)
    check_repo(params.repo, params.mode)
    check_output(params.output)
    check_filter(params.filter)

def print_params(params):
    print("package =", params.package)
    print("repo =", params.repo)
    print("mode =", params.mode)
    print("output =", params.output)
    print("filter =", params.filter)

def main(args=None):
    parser = create_parser()
    params = parser.parse_args(args)
    try:
        check_params(params)
    except ValueError as error:
        print("Ошибка:", error, file=sys.stderr)
        return 1
    print_params(params)
    return 0

if __name__ == "__main__":
    sys.exit(main())
