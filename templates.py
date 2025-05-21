# -*- coding: utf-8 -*-
"""
Templates for generating Python code using LLM models.

This module contains query templates that help generate
better and more reliable Python code using language models.
"""

# Basic template for generating Python code
BASIC_CODE_TEMPLATE = """
Generate working Python code that {task}.

Your code should:
1. Be complete and ready to run
2. Include all necessary imports
3. Use standard Python libraries where possible
4. Include comments explaining key elements
5. Handle basic error cases

Return only Python code in a Markdown code block: ```python ... ```
"""

# Platform-aware template
PLATFORM_AWARE_TEMPLATE = """
Generate working Python code that {task}.

The code will be running on platform: {platform} (operating system: {os}).

Your code should:
1. Be complete and ready to run
2. Include all necessary imports
3. Use libraries compatible with {platform}
4. Include comments explaining key elements
5. Handle basic error cases
6. Avoid using functions specific to other operating systems

Return only Python code in a Markdown code block: ```python ... ```
"""

# Template for generating code with specific dependencies
DEPENDENCY_AWARE_TEMPLATE = """
Generate working Python code that {task}.

You can ONLY use the following external libraries: {dependencies}.
If you need other functionality, implement it yourself.

Your code should:
1. Be complete and ready to run
2. Include all necessary imports (only from allowed libraries)
3. Include comments explaining key elements
4. Handle basic error cases

Return only Python code in a Markdown code block: ```python ... ```
"""

# Template for debugging existing code
DEBUG_CODE_TEMPLATE = """
The following Python code contains an error:

```python
{code}
```

Error:
{error_message}

Fix this code to work correctly. Make sure that:
1. All imports are correct
2. The syntax is valid
3. The logic works as intended
4. The code handles edge cases and potential errors

Return only the corrected Python code in a Markdown code block: ```python ... ```
"""

# Template for generating code with unit tests
TESTABLE_CODE_TEMPLATE = """
Generate working Python code that {task}.

Your code should:
1. Be complete and ready to run
2. Include all necessary imports
3. Be organized into functions or classes with clearly defined responsibilities
4. Include comments explaining key elements
5. Handle basic error cases

Additionally, include unit tests that verify the correctness of the code.

Return only Python code in a Markdown code block: ```python ... ```
"""

# Template for generating code with security considerations
SECURE_CODE_TEMPLATE = """
Generate secure Python code that {task}.

Your code should:
1. Be complete and ready to run
2. Include all necessary imports
3. Implement security best practices
4. Validate input data
5. Handle exceptions in a secure manner
6. Avoid common vulnerabilities (e.g., code injection, uncontrolled file access)
7. Include comments explaining security aspects

Return only Python code in a Markdown code block: ```python ... ```
"""

# Template for generating code with performance considerations
PERFORMANCE_CODE_TEMPLATE = """
Generate efficient Python code that {task}.

Your code should:
1. Be complete and ready to run
2. Include all necessary imports
3. Be optimized for performance
4. Avoid unnecessary operations and excessive memory usage
5. Use appropriate data structures and algorithms
6. Include comments explaining performance-related choices

Return only Python code in a Markdown code block: ```python ... ```
"""

# Template for generating PEP 8 compliant code
PEP8_CODE_TEMPLATE = """
Generate PEP 8 compliant Python code that {task}.

Your code should:
1. Be complete and ready to run
2. Include all necessary imports
3. Strictly follow PEP 8 conventions (naming, indentation, line length, etc.)
4. Include docstrings compliant with PEP 257
5. Handle basic error cases

Return only Python code in a Markdown code block: ```python ... ```
"""

# Function to select the appropriate template based on the query context
def get_template(task: str, template_type: str = "basic", **kwargs) -> str:
    """
    Selects and fills the appropriate template based on type and parameters.
    
    Args:
        task: Description of the task to be performed by the code
        template_type: Template type (basic, platform_aware, dependency_aware, debug, testable, secure, performance, pep8)
        **kwargs: Additional parameters specific to the selected template
    
    Returns:
        Filled template ready to be sent to the LLM model
    """
    templates = {
        "basic": BASIC_CODE_TEMPLATE,
        "platform_aware": PLATFORM_AWARE_TEMPLATE,
        "dependency_aware": DEPENDENCY_AWARE_TEMPLATE,
        "debug": DEBUG_CODE_TEMPLATE,
        "testable": TESTABLE_CODE_TEMPLATE,
        "secure": SECURE_CODE_TEMPLATE,
        "performance": PERFORMANCE_CODE_TEMPLATE,
        "pep8": PEP8_CODE_TEMPLATE
    }
    
    template = templates.get(template_type.lower(), BASIC_CODE_TEMPLATE)
    
    # Fill the template with basic parameters
    prompt = template.format(task=task, **kwargs)
    
    return prompt
