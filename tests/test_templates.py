import pytest
from pylama.templates import get_template


def test_get_template_basic():
    """Test that the basic template is returned correctly."""
    prompt = "Create a hello world program"
    template = get_template(prompt, "basic")
    assert "def main():" in template
    assert prompt in template


def test_get_template_platform_aware():
    """Test that the platform-aware template is returned correctly."""
    prompt = "Create a file reader"
    template = get_template(prompt, "platform_aware")
    assert "import platform" in template
    assert "if platform.system() ==" in template
    assert prompt in template


def test_get_template_dependency_aware():
    """Test that the dependency-aware template is returned correctly."""
    prompt = "Create a web scraper"
    dependencies = "requests,beautifulsoup4"
    template = get_template(prompt, "dependency_aware", dependencies=dependencies)
    assert "requests" in template
    assert "beautifulsoup4" in template
    assert prompt in template


def test_get_template_testable():
    """Test that the testable template is returned correctly."""
    prompt = "Create a calculator function"
    template = get_template(prompt, "testable")
    assert "import unittest" in template
    assert "class Test" in template
    assert prompt in template


def test_get_template_secure():
    """Test that the secure template is returned correctly."""
    prompt = "Create a login form"
    template = get_template(prompt, "secure")
    assert "input validation" in template.lower() or "validate" in template.lower()
    assert prompt in template


def test_get_template_performance():
    """Test that the performance template is returned correctly."""
    prompt = "Create a sorting algorithm"
    template = get_template(prompt, "performance")
    assert "performance" in template.lower() or "efficient" in template.lower()
    assert prompt in template


def test_get_template_pep8():
    """Test that the PEP8 template is returned correctly."""
    prompt = "Create a class for a car"
    template = get_template(prompt, "pep8")
    assert "PEP 8" in template or "style guide" in template.lower()
    assert prompt in template


def test_get_template_invalid():
    """Test that an invalid template type raises a ValueError."""
    prompt = "Create a hello world program"
    with pytest.raises(ValueError):
        get_template(prompt, "invalid_template")
