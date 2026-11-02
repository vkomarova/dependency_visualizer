SEPARATOR = ":"

def is_test_name(name):
    return name.isascii() and name.isalpha() and name.isupper()


def check_test_name(name, line_number):
    if not is_test_name(name):
        raise ValueError("строка " + str(line_number) + ": имя пакета '" +
                         name + "' должно состоять из больших "
                         "латинских букв")


def parse_line(line, line_number):
    if SEPARATOR not in line:
        raise ValueError("строка " + str(line_number) +
                         ": нет двоеточия после имени пакета")
    name, dependencies_text = line.split(SEPARATOR, 1)
    name = name.strip()
    dependencies = dependencies_text.split()
    check_test_name(name, line_number)
    for dependency in dependencies:
        check_test_name(dependency, line_number)
    return name, dependencies


def parse_test_repo(text):
    repo = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        name, dependencies = parse_line(line, line_number)
        repo[name] = dependencies
    return repo


def load_test_repo(path):
    try:
        with open(path, encoding="utf-8") as file:
            text = file.read()
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError("не удалось прочитать файл " + path + " (" +
                         str(error) + ")")
    return parse_test_repo(text)


def get_test_dependencies(repo, name):
    return repo.get(name, [])
