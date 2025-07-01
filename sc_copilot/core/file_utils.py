import re

def extract_yaml_front_matter(content):
    """Extracts YAML front matter from a Markdown string and returns it as a dictionary."""
    yaml_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = yaml_pattern.match(content)
    if not match:
        return {}, content

    yaml_str = match.group(1)
    front_matter = {}
    for line in yaml_str.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if value.startswith('[') and value.endswith(']'):
                front_matter[key] = [item.strip() for item in value[1:-1].split(',')]
            else:
                front_matter[key] = value
    return front_matter, content[match.end():]

