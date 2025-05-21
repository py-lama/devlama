#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyLama API - REST API for Ollama management

This module provides a FastAPI server for managing Ollama models and queries.
"""

import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from pylama.OllamaRunner import OllamaRunner

# Create FastAPI app
app = FastAPI(
    title="PyLama API",
    description="""
    # PyLama API
    
    API for managing Ollama models and executing LLM queries.
    
    ## Features
    
    * List available Ollama models
    * Pull new models from Ollama
    * Execute queries against Ollama models
    * Health check endpoint for monitoring
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Models for request/response
class QueryRequest(BaseModel):
    prompt: str
    model: str = "llama3"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None

class ModelRequest(BaseModel):
    model_name: str

# API endpoints
@app.get("/models", tags=["ollama"])
async def list_models():
    """List all available Ollama models"""
    try:
        runner = OllamaRunner()
        models = runner.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", tags=["ollama"])
async def query_ollama(request: QueryRequest):
    """Query an Ollama model with a prompt"""
    try:
        runner = OllamaRunner()
        kwargs = {}
        if request.max_tokens:
            kwargs["max_tokens"] = request.max_tokens
        if request.system_prompt:
            kwargs["system_prompt"] = request.system_prompt
            
        response = runner.query_ollama(
            request.prompt,
            model=request.model,
            temperature=request.temperature,
            **kwargs
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/pull", tags=["ollama"])
async def pull_model(request: ModelRequest):
    """Pull an Ollama model"""
    try:
        runner = OllamaRunner()
        result = runner.pull_model(request.model_name)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["system"], response_model=Dict[str, str])
async def health_check():
    """
    Check if the API is running
    
    This endpoint provides a simple health check to verify that the API is operational.
    It can be used by monitoring systems to check the service status.
    
    Example response:
    ```json
    {
        "status": "healthy",
        "version": "0.1.0",
        "service": "PyLama API"
    }
    ```
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "PyLama API"
    }

def start_server(host="0.0.0.0", port=8002):
    """Start the PyLama API server"""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
