#!/usr/bin/env python3
"""
Test script to validate form routing logic
"""

import json
import sys
import os

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from form_config import get_form_config, get_supported_forms

def test_form_id_extraction():
    """Test form ID extraction from webhook data"""
    print("Testing form ID extraction...")
    
    # Sample webhook data based on the provided example
    sample_webhook = {
        "event_id": "01JWXH6PP36YCK7KKVSJ8XSBMH",
        "event_type": "form_response",
        "form_response": {
            "form_id": "KdYBmq7K",
            "token": "m0qdb7sv49nz6ccdd3m0qdbsrks2tsq9",
            "definition": {
                "id": "KdYBmq7K",
                "title": "My new form"
            }
        }
    }
    
    # Test extraction logic
    form_id = sample_webhook.get('form_response', {}).get('form_id')
    print(f"Extracted form_id: {form_id}")
    
    if not form_id:
        # Fallback to definition.id
        form_id = sample_webhook.get('form_response', {}).get('definition', {}).get('id')
        print(f"Fallback form_id from definition: {form_id}")
    
    return form_id

def test_form_config_lookup():
    """Test form configuration lookup"""
    print("\nTesting form configuration lookup...")
    
    supported_forms = get_supported_forms()
    print(f"Supported forms: {supported_forms}")
    
    test_form_ids = ['KdYBmq7K', 'EquFr0aR', 'Tikf2fbS', 'InvalidForm']
    
    for form_id in test_form_ids:
        config = get_form_config(form_id)
        if config:
            print(f"✓ Form {form_id}: {config['name']}")
            print(f"  - Prompt template: {config['prompt_template']}")
            print(f"  - Email subject: {config['email_subject']}")
        else:
            print(f"✗ Form {form_id}: Not supported")

def test_template_file_existence():
    """Test if template files exist"""
    print("\nTesting template file existence...")
    
    supported_forms = get_supported_forms()
    
    for form_id in supported_forms:
        config = get_form_config(form_id)
        template_path = config['prompt_template']
        
        if os.path.exists(template_path):
            print(f"✓ Template exists: {template_path}")
            # Check if we can read it
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"  - Template length: {len(content)} characters")
                    if '{webhook_data}' in content:
                        print(f"  - Contains webhook_data placeholder: ✓")
                    else:
                        print(f"  - Missing webhook_data placeholder: ✗")
            except Exception as e:
                print(f"  - Error reading template: {e}")
        else:
            print(f"✗ Template missing: {template_path}")

def test_sample_webhook_processing():
    """Test processing of the sample webhook data"""
    print("\nTesting sample webhook processing...")
    
    # Load the sample webhook data
    sample_file = '/home/ubuntu/upload/pasted_content.txt'
    if os.path.exists(sample_file):
        with open(sample_file, 'r') as f:
            content = f.read()
            
        # Extract JSON from the content
        json_start = content.find('{')
        if json_start != -1:
            json_content = content[json_start:]
            try:
                webhook_data = json.loads(json_content)
                
                # Extract form ID
                form_id = webhook_data.get('form_response', {}).get('form_id')
                print(f"Sample webhook form_id: {form_id}")
                
                # Get config
                config = get_form_config(form_id)
                if config:
                    print(f"✓ Configuration found: {config['name']}")
                    
                    # Extract answers for template
                    answers = {}
                    for answer in webhook_data.get('form_response', {}).get('answers', []):
                        field = answer.get('field', {})
                        field_title = field.get('title', f"field_{field.get('id', 'unknown')}")
                        
                        if answer.get('type') == 'text':
                            answers[field_title] = answer.get('text')
                        elif answer.get('type') == 'email':
                            answers['email'] = answer.get('email')
                        elif answer.get('type') == 'choice':
                            answers[field_title] = answer.get('choice', {}).get('label')
                        elif answer.get('type') == 'boolean':
                            answers[field_title] = answer.get('boolean')
                    
                    print(f"✓ Extracted {len(answers)} answers")
                    print(f"✓ User email: {answers.get('email', 'Not found')}")
                    
                else:
                    print(f"✗ No configuration found for form: {form_id}")
                    
            except json.JSONDecodeError as e:
                print(f"✗ Error parsing JSON: {e}")
    else:
        print(f"✗ Sample file not found: {sample_file}")

if __name__ == "__main__":
    print("=" * 50)
    print("FORM ROUTING VALIDATION TEST")
    print("=" * 50)
    
    test_form_id_extraction()
    test_form_config_lookup()
    test_template_file_existence()
    test_sample_webhook_processing()
    
    print("\n" + "=" * 50)
    print("TEST COMPLETED")
    print("=" * 50)

