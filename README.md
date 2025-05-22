# JSON Transformation Service

A configurable service that receives JSON payloads, applies transformations based on rules defined in a configuration file, and forwards the transformed payloads to target services.

## Features

- Configurable transformation rules via JSON configuration
- Multiple endpoint support with different transformation rules
- Simple dot-notation field mapping (e.g., `$.alert.recipient`)
- Support for conditional transformations
- Function-based transformations (e.g., concatenation)
- Environment variable substitution in headers
- Kubernetes-ready with health and readiness checks
- No external dependencies for path parsing (built-in implementation)

## Project Structure

```
alerta-sms-sender/
├── app.py                # Main FastAPI application
├── config.json           # Configuration file
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker image definition
└── kubernetes.yaml       # Kubernetes deployment manifest
```

## Configuration Format

The configuration file (`config.json`) defines endpoints and their transformation rules:

```json
{
  "endpoints": {
    "endpoint-id": {
      "description": "Description of the endpoint",
      "target_url": "https://target-service.example.com/api/endpoint",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer ${API_KEY}"
      },
      "timeout": 30,
      "transformation": {
        "target_field": "$.source.field",
        "another_field": {
          "function": "concat",
          "fields": [
            "Static text ",
            "$.dynamic.field"
          ]
        },
        "conditional_field": [
          {
            "condition": "$.source.field == \"value\"",
            "value": "result_1"
          },
          {
            "condition": "$.source.field == \"other_value\"",
            "value": "result_2"
          }
        ]
      }
    }
  }
}
```

## Transformation Types

1. **Direct field mapping**: Maps a source field to a target field using JSONPath
   ```json
   "target_field": "$.source.field"
   ```

2. **Function-based transformations**: Apply functions like concatenation
   ```json
   "target_field": {
     "function": "concat",
     "fields": ["prefix ", "$.source.field", " suffix"]
   }
   ```

3. **Conditional transformations**: Apply different values based on conditions
   ```json
   "target_field": [
     {
       "condition": "$.source.field == \"value1\"",
       "value": "result1"
     },
     {
       "condition": "$.source.field == \"value2\"",
       "value": "result2"
     }
   ]
   ```

## Deployment

### Local Development

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the service:
   ```
   CONFIG_PATH=config.json uvicorn app:app --reload
   ```

### Docker

1. Build the Docker image:
   ```
   docker build -t json-transform-service .
   ```

2. Run the container:
   ```
   docker run -p 8000:8000 -e CONFIG_PATH=/app/config.json json-transform-service
   ```

### Kubernetes

1. Apply the Kubernetes manifest:
   ```
   kubectl apply -f kubernetes.yaml
   ```

## Usage

Send a POST request to the service endpoint with a JSON payload:

```
POST /alert-to-sms
{
  "alert": {
    "recipient": "+12345678900",
    "severity": "critical",
    "message": "Server CPU usage above 90%"
  }
}
```

The service will transform and forward this to the configured target service.

## Environment Variables

- `CONFIG_PATH`: Path to the configuration file (default: `config.json`)
- Service-specific API keys referenced in config.json (e.g., `SMS_SERVICE_API_KEY`)
