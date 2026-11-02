import urllib.request
import xml.etree.ElementTree as ElementTree

TIMEOUT_SECONDS = 30


def make_pom_url(repo, package):
    group, artifact, version = package.split(":")
    group_path = group.replace(".", "/")
    file_name = artifact + "-" + version + ".pom"
    parts = [repo.rstrip("/"), group_path, artifact, version, file_name]
    return "/".join(parts)


def download_text(url):
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as answer:
            return answer.read().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError("не удалось загрузить " + url + " (" +
                         str(error) + ")")


def remove_namespaces(root):
    for element in root.iter():
        element.tag = element.tag.split("}")[-1]


def make_dependency_name(dependency):
    group = dependency.findtext("groupId", "").strip()
    artifact = dependency.findtext("artifactId", "").strip()
    version = dependency.findtext("version", "").strip()
    name = group + ":" + artifact
    if version:
        name = name + ":" + version
    return name


def parse_dependencies(pom_text):
    try:
        root = ElementTree.fromstring(pom_text)
    except ElementTree.ParseError:
        raise ValueError("файл POM содержит ошибки XML")
    remove_namespaces(root)
    result = []
    for dependency in root.findall("dependencies/dependency"):
        result.append(make_dependency_name(dependency))
    return result


def get_direct_dependencies(repo, package):
    url = make_pom_url(repo, package)
    pom_text = download_text(url)
    return parse_dependencies(pom_text)