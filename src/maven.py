import urllib.request
import xml.etree.ElementTree as ElementTree

TIMEOUT_SECONDS = 30
PACKAGE_PARTS = 3
SKIPPED_SCOPES = ("test", "provided")
UNKNOWN_VERSION_SIGNS = ("$", "[", "(")


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

def read_properties(root):
    properties = {}
    for element in root.findall("properties/*"):
        properties[element.tag] = (element.text or "").strip()
    group = root.findtext("groupId") or root.findtext("parent/groupId", "")
    version = root.findtext("version") or root.findtext("parent/version", "")
    properties["project.groupId"] = group.strip()
    properties["project.version"] = version.strip()
    return properties

def resolve_value(text, properties):
    if text.startswith("${") and text.endswith("}"):
        name = text[2:-1]
        return properties.get(name, text)
    return text

def is_needed(dependency):
    scope = dependency.findtext("scope", "").strip()
    optional = dependency.findtext("optional", "").strip()
    return scope not in SKIPPED_SCOPES and optional != "true"

def make_dependency_name(dependency, properties):
    group = dependency.findtext("groupId", "").strip()
    artifact = dependency.findtext("artifactId", "").strip()
    version = dependency.findtext("version", "").strip()
    name = resolve_value(group, properties) + ":" + artifact
    if version:
        name = name + ":" + resolve_value(version, properties)
    return name

def parse_dependencies(pom_text):
    try:
        root = ElementTree.fromstring(pom_text)
    except ElementTree.ParseError:
        raise ValueError("файл POM содержит ошибки XML")
    remove_namespaces(root)
    properties = read_properties(root)
    result = []
    for dependency in root.findall("dependencies/dependency"):
        if is_needed(dependency):
            result.append(make_dependency_name(dependency, properties))
    return result

def can_download(package):
    parts = package.split(":")
    if len(parts) != PACKAGE_PARTS or "" in parts:
        return False
    for sign in UNKNOWN_VERSION_SIGNS:
        if sign in parts[-1]:
            return False
    return True

def get_direct_dependencies(repo, package):
    if not can_download(package):
        return []
    url = make_pom_url(repo, package)
    pom_text = download_text(url)
    return parse_dependencies(pom_text)