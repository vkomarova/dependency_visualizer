import argparse
import os
import sys
import maven

MODE_REAL = "real"
MODE_TEST = "test"
URL_PREFIXES = ("http://", "https://")
IMAGE_EXTENSION = ".svg"
PACKAGE_PARTS = 3


def create_parser():
    parser = argparse.ArgumentParser(
        description="Визуализация графа зависимостей пакетов.")
    parser.add_argument("--package", help="имя анализируемого пакета")
    parser.add_argument(
        "--repo", help="URL репозитория или путь к файлу тестового репозитория")
    parser.add_argument("--mode", default=MODE_REAL,
        help="режим работы с репозиторием: real или test (по умолчанию real)")
    parser.add_argument(
        "--output", help="имя файла с изображением графа (.svg)")
    parser.add_argument("--filter", help="подстрока для фильтрации пакетов")
    return parser

def check_maven_name(package):
    parts = package.split(":")
    if len(parts) != PACKAGE_PARTS or "" in parts:
        raise ValueError("имя пакета должно иметь вид "
                         "groupId:artifactId:version")

def check_package(package, mode):
    if not package or not package.strip():
        raise ValueError("не задано имя пакета (--package)")
    if " " in package:
        raise ValueError("имя пакета не должно содержать пробелы")
    if mode == MODE_REAL:
        check_maven_name(package)

def check_mode(mode):
    if mode not in (MODE_REAL, MODE_TEST):
        raise ValueError("режим (--mode) должен быть real или test")

def check_repo(repo, mode):
    if not repo or not repo.strip():
        raise ValueError("не задан репозиторий (--repo)")
    if mode == MODE_REAL and not repo.startswith(URL_PREFIXES):
        raise ValueError("URL репозитория должен начинаться с http:// "
                         "или https://")
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
    check_mode(params.mode)
    check_package(params.package, params.mode)
    check_repo(params.repo, params.mode)
    check_output(params.output)
    check_filter(params.filter)

def get_dependencies(params):
    if params.mode == MODE_TEST:
        raise ValueError("режим test пока не поддерживается")
    return maven.get_direct_dependencies(params.repo, params.package)

def print_dependencies(package, dependencies):
    print("Прямые зависимости пакета " + package + ":")
    if not dependencies:
        print("нет зависимостей")
    for name in dependencies:
        print(name)

def main(args=None):
    parser = create_parser()
    params = parser.parse_args(args)
    try:
        check_params(params)
        dependencies = get_dependencies(params)
    except ValueError as error:
        print("Ошибка:", error, file=sys.stderr)
        return 1
    print_dependencies(params.package, dependencies)
    return 0

if __name__ == "__main__":
    sys.exit(main())