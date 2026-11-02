import argparse
import os
import sys

import graph
import maven
import repo_file

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
    parser.add_argument(
        "--output", help="имя файла с изображением графа (.svg)")
    parser.add_argument("--filter", help="подстрока для фильтрации пакетов")
    return parser

def check_maven_name(package):
    parts = package.split(":")
    if len(parts) != maven.PACKAGE_PARTS or "" in parts:
        raise ValueError("имя пакета должно иметь вид "
                         "groupId:artifactId:version")

def check_package(package, mode):
    if not package or not package.strip():
        raise ValueError("не задано имя пакета (--package)")
    if " " in package:
        raise ValueError("имя пакета не должно содержать пробелы")
    if mode == MODE_REAL:
        check_maven_name(package)
    if mode == MODE_TEST and not repo_file.is_test_name(package):
        raise ValueError("в режиме test имя пакета должно состоять "
                         "из больших латинских букв")

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

def make_real_loader(repo_url):
    def get_dependencies(package):
        """Получить прямые зависимости пакета из репозитория Maven."""
        return maven.get_direct_dependencies(repo_url, package)
    return get_dependencies

def make_test_loader(path, package):
    repo = repo_file.load_test_repo(path)
    if package not in repo:
        raise ValueError("пакет " + package +
                         " не найден в тестовом репозитории")

    def get_dependencies(name):
        return repo_file.get_test_dependencies(repo, name)
    return get_dependencies

def make_loader(params):
    if params.mode == MODE_TEST:
        return make_test_loader(params.repo, params.package)
    return make_real_loader(params.repo)

def print_graph(package, dependency_graph):
    print("Граф зависимостей пакета " + package + ":")
    for name, dependencies in dependency_graph.items():
        if dependencies:
            print(name + " -> " + ", ".join(dependencies))
        else:
            print(name + " -> нет зависимостей")

def main(args=None):
    parser = create_parser()
    params = parser.parse_args(args)
    try:
        check_params(params)
        loader = make_loader(params)
        dependency_graph = graph.build_graph(params.package, loader,
                                             params.filter)
    except ValueError as error:
        print("Ошибка:", error, file=sys.stderr)
        return 1
    print_graph(params.package, dependency_graph)
    return 0

if __name__ == "__main__":
    sys.exit(main())