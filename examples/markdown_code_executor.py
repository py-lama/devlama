#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Code Block Executor

This script extracts Python code blocks from a Markdown file,
executes them using PyBox, and uses PyLLM to fix any issues.
"""

import os
import re
import sys
import logging
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PyBox and PyLLM modules
from devlama.pybox_wrapper import PythonSandbox
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


def execute_code_with_pybox(code):
    """Execute code using PyBox sandbox.
    
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


def fix_code_with_pyllm(code, error_message, is_logic_error=False):
    """Fix code using PyLLM.
    
    Args:
        code (str): The Python code with issues.
        error_message (str): The error message from execution.
        is_logic_error (bool): Whether the error is a logical error rather than a syntax/runtime error.
        
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
        
        # Execute the code
        result = execute_code_with_pybox(code_block)
        
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
                error_message = logic_error_description
            else:
                error_type = result.get('error_type', 'Error')
                error_message = result.get('error_message', result.get('stderr', 'Unknown error'))
                logger.error(f"Code block {i+1} execution failed: {error_type} - {error_message}")
                print(f"\n--- Error ---")
                print(f"{error_type}: {error_message}")
                error_message = f"{error_type}: {error_message}"
            
            # Fix the code using PyLLM
            logger.info(f"Attempting to fix code block {i+1} using PyLLM...")
            fixed_code = fix_code_with_pyllm(code_block, error_message, is_logic_error)
            
            print(f"\n--- Fixed Code ---")
            print(fixed_code)
            
            # Execute the fixed code to verify
            fixed_result = execute_code_with_pybox(fixed_code)
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
