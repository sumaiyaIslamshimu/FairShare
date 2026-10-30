import pytest
from app.scrapers.robot_parser import WildcardRobotParser


def test_shwapno_wildcard_rules():
    robots_txt = """
    User-agent: *
    Disallow: /*?*
    Disallow: /api
    Allow: /*
    """
    parser = WildcardRobotParser(user_agent="FairShareBot")
    parser.parse(robots_txt)

    # Plain paths should be allowed
    assert parser.allowed("https://www.shwapno.com/search") is True

    # Paths containing a question mark should be blocked by /*?*
    assert parser.allowed("https://www.shwapno.com/search?q=rice") is False

    # /api path should be blocked
    assert parser.allowed("https://www.shwapno.com/api/data") is False