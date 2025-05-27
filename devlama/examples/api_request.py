#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API request example
"""

import requests

def get_data_from_api(url):
    """Get data from an API."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

def post_data_to_api(url, data):
    """Post data to an API."""
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

# Example usage
if __name__ == '__main__':
    # Get data from a public API
    api_url = 'https://jsonplaceholder.typicode.com/posts/1'
    result = get_data_from_api(api_url)
    
    if result:
        print("API Response:")
        print(f"Title: {result['title']}")
        print(f"Body: {result['body']}")
        
    # Post data to the API
    post_data = {
        'title': 'New Post',
        'body': 'This is the content of the new post.',
        'userId': 1
    }
    post_result = post_data_to_api('https://jsonplaceholder.typicode.com/posts', post_data)
    
    if post_result:
        print("\nPost Response:")
        print(f"Created post with ID: {post_result['id']}")
