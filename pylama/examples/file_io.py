#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File I/O example
"""

def write_to_file(filename, content):
    """Write content to a file."""
    with open(filename, 'w') as file:
        file.write(content)
    print(f"Content written to {filename}")

def read_from_file(filename):
    """Read content from a file."""
    try:
        with open(filename, 'r') as file:
            content = file.read()
        print(f"Content read from {filename}")
        return content
    except FileNotFoundError:
        print(f"File {filename} not found")
        return None

# Example usage
if __name__ == '__main__':
    # Write to a file
    write_to_file('example.txt', 'Hello, World!\nThis is a sample file.')
    
    # Read from the file
    content = read_from_file('example.txt')
    if content:
        print("File content:")
        print(content)
