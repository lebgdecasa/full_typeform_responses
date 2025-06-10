# Multi-Form Typeform Automation

This updated codebase now supports multiple Typeform forms with form-specific prompt templates and email configurations.

## What's New

### Multi-Form Support
The application now handles three different Typeform forms:
- **KdYBmq7K**: Growth Strategy Assessment (original Epiminded form)
- **EquFr0aR**: Custom form with general response template
- **Tikf2fbS**: Custom form with specialized response template

### Key Features
- **Form-specific routing**: Automatically detects form ID from webhook and routes to appropriate templates
- **Custom prompt templates**: Each form has its own AI prompt template for generating personalized responses
- **Form-specific email subjects**: Different email subjects for each form
- **Template validation**: Built-in validation to ensure templates exist and are properly formatted

## File Structure

```
typeform-automation/
├── app.py                          # Main Flask application (updated)
├── form_config.py                  # Form configuration mapping (new)
├── templates/                      # Template directory (new)
│   └── prompts/
│       ├── KdYBmq7K.txt           # Epiminded Growth Strategy template
│       ├── EquFr0aR.txt           # Form EquFr0aR template
│       └── Tikf2fbS.txt           # Form Tikf2fbS template
├── test_form_routing.py           # Validation test script (new)
├── requirements.txt               # Dependencies (unchanged)
├── Procfile                       # Railway deployment config (unchanged)
├── railway.json                   # Railway config (unchanged)
└── render.yaml                    # Render config (unchanged)
```

## Changes Made

### 1. Form Configuration System (`form_config.py`)
- Created centralized configuration mapping for all supported forms
- Each form has its own prompt template path, email subject, and metadata
- Easy to add new forms by updating the `FORM_CONFIGS` dictionary

### 2. Updated Flask Application (`app.py`)
- **Enhanced webhook handler**: Now extracts form ID from webhook data
- **Template loading**: Dynamically loads prompt templates based on form ID
- **Form validation**: Rejects unsupported forms with clear error messages
- **Improved logging**: Better debugging information for form routing
- **New endpoint**: `/forms` endpoint to list supported forms

### 3. Template System
- **Modular templates**: Each form has its own prompt template file
- **Consistent format**: All templates use `{webhook_data}` placeholder
- **Easy customization**: Templates can be modified without touching code

### 4. Validation and Testing
- **Test script**: `test_form_routing.py` validates the entire routing system
- **Template validation**: Checks template existence and format
- **Webhook processing**: Tests with real webhook data structure

## How It Works

1. **Webhook Reception**: Typeform sends webhook to `/webhook` endpoint
2. **Form ID Extraction**: System extracts form ID from `form_response.form_id`
3. **Configuration Lookup**: Retrieves form-specific configuration
4. **Template Loading**: Loads appropriate prompt template from file
5. **Content Generation**: Uses Gemini AI with form-specific prompt
6. **Email Sending**: Sends email with form-specific subject and sender

## Deployment Instructions

### Environment Variables
Ensure these environment variables are set:
```bash
GEMINI_API_KEY_=your_gemini_api_key
RESEND_API_KEY=your_resend_api_key
MONGODB_URI=your_mongodb_connection_string
TYPEFORM_SECRET=typeformsecret123
YOUR_DOMAIN=https://your-domain.com
```

### Railway Deployment
1. Push the updated code to your repository
2. Railway will automatically detect changes and redeploy
3. Verify deployment by checking `/health` endpoint
4. Test with `/forms` endpoint to see supported forms

### Webhook Configuration
Update your Typeform webhooks to point to:
```
https://typeform-automation-production.up.railway.app/webhook
```

All three forms should use the same webhook URL - the system will automatically route based on form ID.

## Testing

Run the validation test:
```bash
python3 test_form_routing.py
```

This will verify:
- Form ID extraction works correctly
- All templates exist and are properly formatted
- Configuration mapping is correct
- Sample webhook processing works

## Adding New Forms

To add a new form:

1. **Create prompt template**: Add new template file in `templates/prompts/`
2. **Update configuration**: Add entry to `FORM_CONFIGS` in `form_config.py`
3. **Test**: Run validation script to ensure everything works

Example configuration entry:
```python
'NewFormID': {
    'name': 'New Form Name',
    'prompt_template': 'templates/prompts/NewFormID.txt',
    'email_subject': 'Your New Form Response',
    'from_email': 'sender@domain.com',
    'description': 'Description of the new form'
}
```

## Monitoring

The application logs detailed information about:
- Form ID extraction
- Template loading
- Email generation and sending
- Error handling

Check your deployment logs to monitor form processing and troubleshoot issues.

## Support

If you encounter issues:
1. Check the logs for error messages
2. Verify form ID matches configuration
3. Ensure templates exist and are properly formatted
4. Test with the validation script

