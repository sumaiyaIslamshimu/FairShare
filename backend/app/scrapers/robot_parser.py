import re
from urllib.parse import urlparse, unquote


class WildcardRobotParser:
    """
    A simple robots.txt parser that supports RFC 9309 wildcards (* and $).
    """

    def __init__(self, user_agent="*"):
        self.user_agent = user_agent.lower()
        self.rules = []  # List of tuples: (pattern_regex, is_allowed, path_length)

    def parse(self, robots_text: str):
        current_agent_matches = False

        for line in robots_text.splitlines():
            line = line.split('#', 1)[0].strip()
            if not line:
                continue

            parts = line.split(':', 1)
            if len(parts) != 2:
                continue

            field = parts[0].strip().lower()
            value = parts[1].strip()

            if field == 'user-agent':
                val_lower = value.lower()
                current_agent_matches = (val_lower == self.user_agent or val_lower == '*')
            elif current_agent_matches and field in ('allow', 'disallow'):
                if not value:
                    continue  # Empty rule means allow all for this directive type, handled by default

                # Convert RFC 9309 wildcard to regex
                # 1. Escape regex specials
                regex_pattern = re.escape(value)
                # 2. Unescape the wildcards we care about
                regex_pattern = regex_pattern.replace(r'\*', '.*')
                if regex_pattern.endswith(r'\$'):
                    regex_pattern = regex_pattern[:-2] + '$'

                # Rules match from the beginning of the path
                regex_pattern = '^' + regex_pattern

                is_allow = (field == 'allow')
                # For sorting by specificity (longest match wins)
                self.rules.append((re.compile(regex_pattern), is_allow, len(value)))

    def allowed(self, url: str) -> bool:
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        if parsed_url.query:
            path += '?' + unquote(parsed_url.query)

        if not path:
            path = '/'

        # Sort rules by path length descending (most specific first)
        sorted_rules = sorted(self.rules, key=lambda x: x[2], reverse=True)

        for pattern, is_allow, _ in sorted_rules:
            if pattern.search(path):
                return is_allow

        return True  # Default allow if no rules match