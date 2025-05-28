#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper for getllm functionality to handle import issues.

This module provides a clean interface to the getllm package functions
regardless of how the package is installed or structured.
"""

import os
import sys
import importlib.util
from typing import List, Optional, Dict, Any

# Add parent directory to sys.path to find getllm package
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Check if getllm/getllm/models.py exists and import directly
models_path = os.path.join(parent_dir, 'getllm', 'getllm', 'models.py')
if os.path.exists(models_path):
    # Import directly from the file
    spec = importlib.util.spec_from_file_location("getllm.models", models_path)
    models_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models_module)
    
    # Get the functions we need
    get_models = models_module.get_models
    get_default_model = models_module.get_default_model
    set_default_model = models_module.set_default_model
    install_model = models_module.install_model
    list_installed_models = models_module.list_installed_models
    update_models_from_ollama = models_module.update_models_from_ollama
else:
    # Fallback implementations if the module can't be found
    def get_models() -> List[str]:
        """Get a list of available models."""
        return ["llama2", "codellama", "phi"]
    
    def get_default_model() -> str:
        """Get the default model."""
        return "llama2"
    
    def set_default_model(model: str) -> None:
        """Set the default model."""
        pass
    
    def install_model(model: str) -> bool:
        """Install a model."""
        return False
    
    def list_installed_models() -> List[str]:
        """List installed models."""
        return ["llama2"]
    
    def update_models_from_ollama() -> Dict[str, Any]:
        """Update models from Ollama."""
        return {}
