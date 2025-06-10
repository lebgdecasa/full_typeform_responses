# Form Configuration
# Maps form IDs to their respective templates and settings

FORM_CONFIGS = {
    'KdYBmq7K': {
        'name': 'Growth Strategy Assessment',
        'prompt_template': 'templates/prompts/KdYBmq7K.txt',
        'email_subject': 'Your Growth Strategy Assessment Results',
        'from_email': 'Reda Bennani <redabennani@epinnovators.org>',
        'description': 'Epiminded Growth Strategist questionnaire with scoring system'
    },
    'EquFr0aR': {
        'name': 'Form EquFr0aR',
        'prompt_template': 'templates/prompts/EquFr0aR.txt',
        'email_subject': 'Thank you for your submission !',
        'from_email': 'Reda Bennani <redabennani@epinnovators.org>',
        'description': 'Custom form EquFr0aR responses'
    },
    'Tikf2fbS': {
        'name': 'Form Tikf2fbS',
        'prompt_template': 'templates/prompts/Tikf2fbS.txt',
        'email_subject': 'Your Form Response',
        'from_email': 'Reda Bennani <redabennani@epinnovators.org>',
        'description': 'Custom form Tikf2fbS responses'
    }
}

def get_form_config(form_id):
    """
    Get configuration for a specific form ID

    Args:
        form_id (str): The Typeform form ID

    Returns:
        dict: Form configuration or None if not found
    """
    return FORM_CONFIGS.get(form_id)

def get_supported_forms():
    """
    Get list of all supported form IDs

    Returns:
        list: List of supported form IDs
    """
    return list(FORM_CONFIGS.keys())

def extract_form_id_from_url(form_url):
    """
    Extract form ID from Typeform URL

    Args:
        form_url (str): Full Typeform URL

    Returns:
        str: Form ID or None if not found
    """
    if '/to/' in form_url:
        return form_url.split('/to/')[-1]
    return None
