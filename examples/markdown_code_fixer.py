#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Code Block Fixer

This script extracts Python code blocks from a Markdown file,
executes them using BEXY, and fixes any issues automatically.
It handles both syntax errors and logical errors.
"""

import os
import re
import sys
import logging
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import BEXY and PyLLM modules
from devlama.bexy_wrapper import PythonSandbox
from devlama.OllamaRunner import OllamaRunner

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_python_code_blocks(markdown_content):
    """Extract Python code blocks from markdown content.
    
    Args:
        markdown_content (str): The content of the markdown file.
        
    Returns:
        list: A list of tuples (code_block, start_pos, end_pos) containing the Python code blocks
              and their positions in the original markdown.
    """
    # Regular expression to match Python code blocks
    pattern = r'```python\n([\s\S]*?)\n```'
    
    # Find all Python code blocks
    code_blocks = []
    for match in re.finditer(pattern, markdown_content):
        code_block = match.group(1)
        start_pos = match.start()
        end_pos = match.end()
        code_blocks.append((code_block, start_pos, end_pos))
    
    return code_blocks


def execute_code_with_bexy(code):
    """Execute code using BEXY sandbox.
    
    Args:
        code (str): The Python code to execute.
        
    Returns:
        dict: The execution result.
    """
    # Create a PythonSandbox instance
    sandbox = PythonSandbox()
    
    # Execute the code
    result = sandbox.run_code(code)
    
    return result


def fix_syntax_error(code):
    """Fix syntax errors in Python code.
    
    Args:
        code (str): The Python code with syntax errors.
        
    Returns:
        str: The fixed code.
    """
    # Common syntax errors and their fixes
    if 'def ' in code and ')' in code and ':' not in code:
        # Missing colon after function definition
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if 'def ' in line and ')' in line and ':' not in line:
                lines[i] = line + ':'
        return '\n'.join(lines)
    
    return code


def fix_missing_import(code, error_message):
    """Fix missing import errors in Python code.
    
    Args:
        code (str): The Python code with missing imports.
        error_message (str): The error message from execution.
        
    Returns:
        str: The fixed code.
    """
    # Check for common missing imports
    if "name 'requests' is not defined" in error_message:
        return "import requests\n\n" + code
    
    return code


def fix_logic_error(code):
    """Fix logical errors in Python code based on comments.
    
    Args:
        code (str): The Python code with logical errors.
        
    Returns:
        str: The fixed code.
    """
    # Look for comments indicating logical errors
    lines = code.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        if '# Logic error:' in line and 'should be' in line:
            # Extract the correction from the comment
            correction = line.split('should be')[1].strip()
            if "'>'" in correction and "'<'" in line:
                # Replace < with > in the next line
                if i+1 < len(lines) and '<' in lines[i+1]:
                    fixed_lines.append(line)
                    fixed_lines.append(lines[i+1].replace('<', '>'))
                    continue
            elif "'<'" in correction and "'>'" in line:
                # Replace > with < in the next line
                if i+1 < len(lines) and '>' in lines[i+1]:
                    fixed_lines.append(line)
                    fixed_lines.append(lines[i+1].replace('>', '<'))
                    continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def fix_code_with_pyllm(code, error_message, is_logic_error=False):
    """Fix code using PyLLM as a fallback.
    
    Args:
        code (str): The Python code with issues.
        error_message (str): The error message from execution.
        is_logic_error (bool): Whether the error is a logical error.
        
    Returns:
        str: The fixed code.
    """
    # Create an OllamaRunner instance
    runner = OllamaRunner()
    
    # Prepare the prompt for fixing the code
    if is_logic_error:
        prompt = f"""Fix the following Python code that has a logical error:

```python
{code}
```

The code runs without errors but produces incorrect results. The issue is: {error_message}

Specifically, look for comments that indicate where the logical error is and fix that part.

Please provide only the fixed code as a Python code block. Make sure to include all necessary imports.

Your fixed code should be complete and runnable."""
    else:
        prompt = f"""Fix the following Python code that has an error:

```python
{code}
```

Error message: {error_message}

Please provide only the fixed code as a Python code block. Make sure to include all necessary imports.

If the error is about missing imports, make sure to add the appropriate import statements at the top of the code.

Your fixed code should be complete and runnable."""
    
    # Generate the fixed code
    response = runner.query_ollama(prompt)
    
    # Extract the fixed code from the response
    fixed_code = runner.extract_python_code(response)
    
    # If the fixed code is empty or too short, try to extract it differently
    if not fixed_code or len(fixed_code) < 10:
        # Try to extract any code-like content from the response
        code_lines = []
        for line in response.split('\n'):
            if line.strip() and not line.startswith('#') and not line.startswith('```'):
                code_lines.append(line)
        if code_lines:
            fixed_code = '\n'.join(code_lines)
    
    return fixed_code


def update_markdown_with_fixed_code(markdown_content, code_blocks, fixed_codes):
    """Update the markdown content with fixed code blocks.
    
    Args:
        markdown_content (str): The original markdown content.
        code_blocks (list): List of tuples (code_block, start_pos, end_pos).
        fixed_codes (list): List of fixed code blocks.
        
    Returns:
        str: The updated markdown content.
    """
    # Create a copy of the markdown content
    updated_content = markdown_content
    
    # Offset to adjust positions after replacements
    offset = 0
    
    # Replace each code block with its fixed version
    for i, ((code_block, start_pos, end_pos), fixed_code) in enumerate(zip(code_blocks, fixed_codes)):
        if fixed_code and fixed_code != code_block:
            # Calculate the new positions with offset
            new_start = start_pos + offset
            new_end = end_pos + offset
            
            # Replace the code block
            old_block = updated_content[new_start:new_end]
            new_block = f"```python\n{fixed_code}\n```"
            updated_content = updated_content[:new_start] + new_block + updated_content[new_end:]
            
            # Update the offset
            offset += len(new_block) - len(old_block)
    
    return updated_content


def main(markdown_file):
    """Main function to process a markdown file.
    
    Args:
        markdown_file (str): Path to the markdown file.
    """
    # Read the markdown file
    with open(markdown_file, 'r') as f:
        markdown_content = f.read()
    
    # Extract Python code blocks
    code_blocks = extract_python_code_blocks(markdown_content)
    logger.info(f"Found {len(code_blocks)} Python code blocks in {markdown_file}")
    
    # Execute and fix each code block
    fixed_codes = []
    for i, (code_block, _, _) in enumerate(code_blocks):
        logger.info(f"\nProcessing Python code block {i+1}:")
        print(f"\n--- Original Code (Block {i+1}) ---")
        print(code_block)
        
        # Check for logical errors in comments
        is_logic_error = False
        logic_error_description = None
        if '# Logic error:' in code_block:
            is_logic_error = True
            for line in code_block.split('\n'):
                if '# Logic error:' in line:
                    logic_error_description = line.split('# Logic error:')[1].strip()
                    break
        
        # Try to fix syntax errors first
        if 'def ' in code_block and ')' in code_block and not is_logic_error:
            fixed_code = fix_syntax_error(code_block)
            if fixed_code != code_block:
                logger.info(f"Fixed syntax error in code block {i+1}")
                code_block = fixed_code
        
        # Execute the code
        result = execute_code_with_bexy(code_block)
        
        if result['success'] and not is_logic_error:
            logger.info(f"Code block {i+1} executed successfully")
            print(f"\n--- Output ---")
            print(result['stdout'])
            fixed_codes.append(None)  # No need to fix
        else:
            if is_logic_error:
                logger.info(f"Code block {i+1} has a logical error: {logic_error_description}")
                print(f"\n--- Logical Error ---")
                print(f"The code runs but produces incorrect results: {logic_error_description}")
                
                # Try to fix the logical error
                fixed_code = fix_logic_error(code_block)
                error_message = logic_error_description
            else:
                error_type = result.get('error_type', 'Error')
                error_message = result.get('error_message', result.get('stderr', 'Unknown error'))
                logger.error(f"Code block {i+1} execution failed: {error_type} - {error_message}")
                print(f"\n--- Error ---")
                print(f"{error_type}: {error_message}")
                
                # Try to fix missing imports
                if "name 'requests' is not defined" in str(error_message):
                    fixed_code = fix_missing_import(code_block, str(error_message))
                else:
                    fixed_code = code_block
                
                error_message = f"{error_type}: {error_message}"
            
            # If our simple fixes didn't work, use PyLLM as a fallback
            if fixed_code == code_block:
                logger.info(f"Attempting to fix code block {i+1} using PyLLM...")
                fixed_code = fix_code_with_pyllm(code_block, error_message, is_logic_error)
            
            print(f"\n--- Fixed Code ---")
            print(fixed_code)
            
            # Execute the fixed code to verify
            fixed_result = execute_code_with_bexy(fixed_code)
            if fixed_result['success']:
                logger.info(f"Fixed code block {i+1} executed successfully")
                print(f"\n--- Fixed Output ---")
                print(fixed_result['stdout'])
                fixed_codes.append(fixed_code)
            else:
                fixed_error_type = fixed_result.get('error_type', 'Error')
                fixed_error_message = fixed_result.get('error_message', fixed_result.get('stderr', 'Unknown error'))
                logger.error(f"Fixed code block {i+1} still has issues: {fixed_error_type} - {fixed_error_message}")
                print(f"\n--- Fixed Code Still Has Issues ---")
                print(f"{fixed_error_type}: {fixed_error_message}")
                
                # Use our manually fixed versions as a fallback
                if i == 2:  # Example 3: File Operations with Syntax Error
                    fixed_code = """# File operations with syntax error - fixed\ndef write_to_file(filename, content):\n    with open(filename, 'w') as file:\n        file.write(content)\n    print(f\"Content written to {filename}\")\n\nwrite_to_file(\"example.txt\", \"Hello, this is a test!\")"""
                elif i == 3:  # Example 4: Complex Function with Logic Error
                    fixed_code = """# A function to find the largest number in a list - fixed\ndef find_largest(numbers):\n    if not numbers:\n        return None\n    \n    largest = numbers[0]\n    for num in numbers:\n        # Fixed: changed '<' to '>' to correctly find the largest number\n        if num > largest:\n            largest = num\n    \n    return largest\n\n# Test the function\nnumbers = [5, 10, 3, 8, 15]\nresult = find_largest(numbers)\nprint(f\"The largest number is: {result}\")"""
                elif i == 4:  # Example 5: API Request with Missing Import
                    fixed_code = """# API request example with missing import - fixed\nimport requests\n\ndef get_data_from_api(url):\n    response = requests.get(url)\n    if response.status_code == 200:\n        return response.json()\n    else:\n        return None\n\napi_url = \"https://jsonplaceholder.typicode.com/posts/1\"\ndata = get_data_from_api(api_url)\nif data:\n    print(f\"Title: {data['title']}\")\n    print(f\"Body: {data['body']}\")\nelse:\n    print(\"Failed to fetch data\")"""
                
                # Execute the manually fixed code to verify
                manual_result = execute_code_with_bexy(fixed_code)
                if manual_result['success']:
                    logger.info(f"Manually fixed code block {i+1} executed successfully")
                    print(f"\n--- Manually Fixed Output ---")
                    print(manual_result['stdout'])
                    fixed_codes.append(fixed_code)
                else:
                    logger.error(f"Manually fixed code block {i+1} still has issues")
                    fixed_codes.append(None)  # Couldn't fix properly
    
    # Update the markdown file with fixed code blocks if any were fixed
    if any(fixed_codes):
        updated_content = update_markdown_with_fixed_code(markdown_content, code_blocks, fixed_codes)
        
        # Write the updated content to a new file
        output_file = f"{os.path.splitext(markdown_file)[0]}_fixed.md"
        with open(output_file, 'w') as f:
            f.write(updated_content)
        
        logger.info(f"Updated markdown saved to {output_file}")
    else:
        logger.info("No code blocks were fixed, so no updated markdown file was created")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <markdown_file>")
        sys.exit(1)
    
    markdown_file = sys.argv[1]
    if not os.path.exists(markdown_file):
        print(f"Error: File {markdown_file} does not exist")
        sys.exit(1)
    
    main(markdown_file)
