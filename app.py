from fastapi import FastAPI, Request, HTTPException, status, Response
import httpx
import json
import os
import logging
import re
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="JSON Transformation Service", 
              description="A configurable service to receive, transform, and forward JSON payloads")

# Global configuration variable
config = {}

class HealthResponse(BaseModel):
    status: str


def load_config(config_path: str) -> Dict[str, Any]:
    """Load the configuration file"""
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        raise


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """
    Extract value from nested dictionary using dot notation path
    Supports paths like: $.alert.recipient, $.alert.items[0].name
    """
    if not path.startswith('$'):
        return path  # Return as literal value
    
    try:
        # Remove the $ prefix and split by dots
        path_parts = path[1:].split('.')
        current = data
        
        for part in path_parts:
            if not part:  # Skip empty parts (like from $.field)
                continue
                
            # Handle array indexing like "items[0]"
            if '[' in part and ']' in part:
                key_part = part[:part.index('[')]
                index_part = part[part.index('[') + 1:part.index(']')]
                
                # Navigate to the key first (if it exists)
                if key_part:
                    current = current[key_part]
                
                # Then apply the index
                try:
                    index = int(index_part)
                    current = current[index]
                except (ValueError, IndexError):
                    return None
            else:
                # Simple key access
                current = current[part]
                
        return current
    except (KeyError, TypeError, IndexError) as e:
        logger.debug(f"Path extraction failed for '{path}': {str(e)}")
        return None


def apply_transformation(data: Dict[str, Any], transformation_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Apply transformation rules to the input data"""
    result = {}
    
    try:
        for target_field, source_expr in transformation_rules.items():
            # Handle direct field mapping (string)
            if isinstance(source_expr, str):
                value = get_nested_value(data, source_expr)
                if value is not None:
                    result[target_field] = value
            
            # Handle function transformations (dict with 'function' key)
            elif isinstance(source_expr, dict) and 'function' in source_expr:
                if source_expr['function'] == 'concat':
                    values = []
                    for field in source_expr.get('fields', []):
                        value = get_nested_value(data, field)
                        if value is not None:
                            values.append(str(value))
                    result[target_field] = ''.join(values)
                else:
                    logger.warning(f"Unknown function: {source_expr['function']}")
                    
            # Handle conditional transformations (list of conditions)
            elif isinstance(source_expr, list):
                for condition in source_expr:
                    if isinstance(condition, dict) and 'condition' in condition and 'value' in condition:
                        if evaluate_condition(condition['condition'], data):
                            result[target_field] = condition['value']
                            break
                            
    except Exception as e:
        logger.error(f"Error during transformation: {str(e)}")
        raise
    
    return result


def evaluate_condition(condition: str, data: Dict[str, Any]) -> bool:
    """
    Evaluate a simple condition against the data
    Supports simple equality checks like: $.field == "value"
    """
    try:
        if "==" in condition:
            left, right = condition.split("==", 1)
            left = left.strip()
            right = right.strip()
            
            # Get left side value
            left_value = get_nested_value(data, left)
            
            # Get right side value
            if right.startswith('"') and right.endswith('"'):
                right_value = right[1:-1]  # Remove quotes
            elif right.startswith('$'):
                right_value = get_nested_value(data, right)
            else:
                right_value = right
                
            return str(left_value) == str(right_value)
        
        return False
    except Exception as e:
        logger.warning(f"Error evaluating condition '{condition}': {str(e)}")
        return False


def substitute_env_vars(text: str) -> str:
    """Substitute environment variables in text like ${VAR_NAME}"""
    def replace_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))
    
    return re.sub(r'\$\{([^}]+)\}', replace_var, text)


@app.on_event("startup")
async def startup_event():
    """Load configuration on startup"""
    global config
    config_path = os.environ.get("CONFIG_PATH", "config.json")
    logger.info(f"Loading configuration from {config_path}")
    config = load_config(config_path)
    logger.info("Service started successfully")


@app.get("/health", status_code=status.HTTP_200_OK, response_model=HealthResponse)
async def health_check():
    """Kubernetes health check endpoint"""
    return {"status": "ok"}


@app.get("/ready", status_code=status.HTTP_200_OK, response_model=HealthResponse)
async def readiness_check():
    """Kubernetes readiness check endpoint"""
    if not config:
        raise HTTPException(status_code=503, detail="Service not ready - configuration not loaded")
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint showing service info"""
    return {
        "service": "JSON Transformation Service",
        "status": "running",
        "endpoints": list(config.get("endpoints", {}).keys()) if config else []
    }


@app.post("/{endpoint_id}")
async def process_request(request: Request, endpoint_id: str):
    """Process the incoming request, transform it, and forward it"""
    
    # Verify the endpoint exists in configuration
    if endpoint_id not in config.get("endpoints", {}):
        raise HTTPException(status_code=404, detail=f"Endpoint {endpoint_id} not found")
    
    endpoint_config = config["endpoints"][endpoint_id]
    
    # Read the request body
    try:
        payload = await request.json()
        logger.info(f"Received payload for endpoint {endpoint_id}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Apply transformation
    try:
        transformation_rules = endpoint_config.get("transformation", {})
        transformed_payload = apply_transformation(payload, transformation_rules)
        logger.info(f"Transformed payload for endpoint {endpoint_id}")
        logger.debug(f"Original: {payload}")
        logger.debug(f"Transformed: {transformed_payload}")
    except Exception as e:
        logger.error(f"Transformation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transformation error: {str(e)}")
    
    # Forward the transformed payload
    try:
        target_url = endpoint_config.get("target_url")
        if not target_url:
            raise HTTPException(status_code=500, detail="Target URL not configured")
        
        headers = endpoint_config.get("headers", {})
        # Substitute environment variables in headers
        headers = {k: substitute_env_vars(str(v)) for k, v in headers.items()}
        
        timeout = endpoint_config.get("timeout", 30)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                target_url,
                json=transformed_payload,
                headers=headers,
                timeout=timeout
            )
            
            logger.info(f"Forwarded to {target_url}, status: {response.status_code}")
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to target service timed out")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Error forwarding request: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
