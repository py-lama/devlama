#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Default example template
"""

def main(task_description):
    """Main function that demonstrates the requested functionality."""
    print("Hello, World!")
    print(f"This is a simple example for: {task_description}")
    
    # Add your code here to implement the requested functionality
    result = f"Example implementation for {task_description}"
    return result

if __name__ == '__main__':
    # Replace this with your actual task description
    task = "your task description"
    output = main(task)
    print(f"Result: {output}")
