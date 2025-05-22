#!/usr/bin/env python3
"""
Local test script to verify the transformation logic works correctly
"""

import json
import sys
import os

# Add current directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import apply_transformation, get_value_by_path

def test_transformations():
    """Test the transformation functions"""
    
    # Sample input data
    test_data = {
        "alert": {
            "recipient": "+12345678900",
            "severity": "critical",
            "message": "Server CPU usage above 90%"
        }
    }
    
    # Sample transformation rules
    transformation_rules = {
        "recipient": "$.alert.recipient",
        "message": {
            "function": "concat",
            "fields": [
                "ALERT: ",
                "$.alert.severity",
                " - ",
                "$.alert.message"
            ]
        },
        "priority": [
            {
                "condition": "$.alert.severity == \"critical\"",
                "value": "high"
            },
            {
                "condition": "$.alert.severity == \"warning\"",
                "value": "medium"
            },
            {
                "condition": "$.alert.severity == \"info\"",
                "value": "low"
            }
        ],
        "sender": "AlertSystem"
    }
    
    print("Original data:")
    print(json.dumps(test_data, indent=2))
    
    print("\nTransformation rules:")
    print(json.dumps(transformation_rules, indent=2))
    
    # Test individual path extraction
    print("\nTesting path extraction:")
    print(f"$.alert.recipient -> {get_value_by_path(test_data, '$.alert.recipient')}")
    print(f"$.alert.severity -> {get_value_by_path(test_data, '$.alert.severity')}")
    print(f"$.alert.message -> {get_value_by_path(test_data, '$.alert.message')}")
    
    # Test transformation
    try:
        result = apply_transformation(test_data, transformation_rules)
        print("\nTransformation result:")
        print(json.dumps(result, indent=2))
        return True
    except Exception as e:
        print(f"\nTransformation failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_transformations()
    sys.exit(0 if success else 1)
