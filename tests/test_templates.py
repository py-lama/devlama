import pytest
from devlama.templates import get_template


def test_get_template_basic():
    """Test that the basic template is returned correctly."""
    prompt = "Create a hello world program"
    template = get_template(prompt, "basic")
    assert "Generate working Python code" in template
    assert "Include all necessary imports" in template
    assert prompt in template


def test_get_template_platform_aware():
    """Test that the platform-aware template is returned correctly."""
    prompt = "Create a file reader"
    # Provide the required platform and os parameters
    template = get_template(prompt, "platform_aware", platform="Linux", os="Linux")
    assert "platform: Linux" in template
    assert "operating system: Linux" in template
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
    assert "include unit tests" in template.lower()
    assert "verify the correctness" in template
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
    """Test that an invalid template type falls back to the basic template."""
    prompt = "Create a hello world program"
    # The current implementation falls back to basic template instead of raising ValueError
    template = get_template(prompt, "invalid_template_type")
    assert "Generate working Python code" in template
    assert prompt in template
