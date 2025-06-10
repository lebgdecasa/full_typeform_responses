import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
import google.generativeai as genai
import resend
from pymongo import MongoClient
import hashlib
import requests
from form_config import get_form_config, get_supported_forms

app = Flask(__name__)

# Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY_')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
TYPEFORM_SECRET = os.environ.get('TYPEFORM_SECRET', '')  # For webhook verification
YOUR_DOMAIN = os.environ.get('YOUR_DOMAIN', 'http://localhost:5000')

# Initialize clients
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
resend.api_key = RESEND_API_KEY
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client.typeform_automation
submissions_collection = db.submissions
feedback_collection = db.feedback

# Email template with feedback buttons
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .content {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .feedback-section {{
            background-color: #f4f4f4;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
            text-align: center;
        }}
        .feedback-buttons {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 15px;
        }}
        .feedback-btn {{
            display: inline-block;
            padding: 15px 25px;
            text-decoration: none;
            border-radius: 5px;
            font-size: 24px;
            transition: transform 0.2s;
        }}
        .feedback-btn:hover {{ transform: scale(1.1); }}
    </style>
</head>
<body>
    <div class="content">
        {content}

        <div class="feedback-section">
            <h3>How was this response?</h3>
            <div class="feedback-buttons">
                <a href="{feedback_url}?rating=positive&id={submission_id}" class="feedback-btn">😊</a>
                <a href="{feedback_url}?rating=neutral&id={submission_id}" class="feedback-btn">😐</a>
                <a href="{feedback_url}?rating=negative&id={submission_id}" class="feedback-btn">☹️</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

def verify_typeform_signature(request_data, signature):
    """Verify Typeform webhook signature"""
    if not TYPEFORM_SECRET:
        return True  # Skip verification if no secret is set

    computed_signature = hashlib.sha256(
        f"{TYPEFORM_SECRET}{request_data}".encode()
    ).hexdigest()

    return computed_signature == signature

def extract_form_id_from_webhook(webhook_data):
    """Extract form ID from webhook data"""
    form_id = webhook_data.get('form_id')
    if form_id:
        return form_id
    
    # Try to extract from form definition if available
    form_definition = webhook_data.get('form_definition', {})
    if form_definition:
        form_id = form_definition.get('id')
        if form_id:
            return form_id
    
    return None

def load_prompt_template(template_path):
    """Load prompt template from file"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Template file not found: {template_path}")
        return None
    except Exception as e:
        print(f"Error loading template {template_path}: {e}")
        return None

def extract_typeform_data(webhook_data):
    """Extract relevant data from Typeform webhook"""
    form_response = webhook_data.get('form_response', {})

    # Extract answers
    answers = {}
    for answer in form_response.get('answers', []):
        field = answer.get('field', {})
        field_title = field.get('title', f"field_{field.get('id', 'unknown')}")

        # Handle different answer types
        if answer.get('type') == 'text':
            answers[field_title] = answer.get('text')
        elif answer.get('type') == 'email':
            answers['email'] = answer.get('email')
        elif answer.get('type') == 'choice':
            answers[field_title] = answer.get('choice', {}).get('label')
        elif answer.get('type') == 'choices':
            answers[field_title] = [c.get('label') for c in answer.get('choices', [])]
        elif answer.get('type') == 'number':
            answers[field_title] = answer.get('number')
        # Add more types as needed

    # Extract metadata
    metadata = {
        'submitted_at': form_response.get('submitted_at'),
        'form_id': webhook_data.get('form_id'),
        'response_id': form_response.get('response_id'),
        'token': form_response.get('token')
    }

    return answers, metadata

def generate_email_content(answers, form_config, webhook_data):
    """Generate personalized email content using Google Gemini with form-specific template"""
    
    # Load the prompt template for this form
    prompt_template = load_prompt_template(form_config['prompt_template'])
    if not prompt_template:
        # Fallback to a generic template
        prompt_template = """
        You are a helpful assistant. Please analyze the following form responses and create a personalized HTML email response.
        
        Form responses:
        {webhook_data}
        
        Please create a professional and helpful response in HTML format.
        """

    # Prepare the context
    answers_text = "\n".join([f"{k}: {v}" for k, v in answers.items() if k != 'email'])

    # Format the prompt with the webhook data
    full_prompt = prompt_template.format(webhook_data=answers_text)

    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"Error generating content: {e}")
        return f"Thank you for your submission to {form_config['name']}. We received your responses and will get back to you soon."

def send_email(to_email, subject, content, submission_id, from_email):
    """Send email using Resend with feedback buttons"""
    feedback_url = f"{YOUR_DOMAIN}/feedback"

    html_content = EMAIL_TEMPLATE.format(
        content=content,
        feedback_url=feedback_url,
        submission_id=submission_id
    )

    try:
        response = resend.Emails.send({
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "html": html_content
        })
        return response
    except Exception as e:
        print(f"Error sending email: {e}")
        return None

@app.route('/webhook', methods=['POST'])
def typeform_webhook():
    """Handle Typeform webhook with multi-form support"""
    print("\n" + "="*50)
    print("WEBHOOK RECEIVED!")

    try:
        # Log headers
        print("Headers:", dict(request.headers))

        # Skip signature verification for now
        # signature = request.headers.get('Typeform-Signature')
        # if signature and not verify_typeform_signature(request.data, signature):
        #     return jsonify({'error': 'Invalid signature'}), 401

        # Get JSON data
        print("Getting JSON data...")
        webhook_data = request.get_json()
        print("JSON parsed successfully")
        print(f"Event type: {webhook_data.get('event_type')}")

        # Extract form ID
        form_id = extract_form_id_from_webhook(webhook_data)
        print(f"Form ID: {form_id}")

        if not form_id:
            print("No form ID found in webhook data")
            return jsonify({'error': 'No form ID found'}), 400

        # Get form configuration
        form_config = get_form_config(form_id)
        if not form_config:
            print(f"Unsupported form ID: {form_id}")
            print(f"Supported forms: {get_supported_forms()}")
            return jsonify({'error': f'Unsupported form ID: {form_id}'}), 400

        print(f"Using configuration for form: {form_config['name']}")

        # Extract data
        print("Extracting form data...")
        answers, metadata = extract_typeform_data(webhook_data)
        print(f"Extracted {len(answers)} answers")
        print(f"Answers: {answers}")

        # Get email address
        user_email = answers.get('email')
        print(f"User email: {user_email}")

        if not user_email:
            print("No email found in submission")
            return jsonify({'error': 'No email found'}), 400

        # Generate submission ID
        submission_id = str(uuid.uuid4())
        print(f"Submission ID: {submission_id}")

        # Store in MongoDB
        print("Storing in MongoDB...")
        submission_doc = {
            '_id': submission_id,
            'form_id': form_id,
            'form_name': form_config['name'],
            'answers': answers,
            'metadata': metadata,
            'created_at': datetime.utcnow(),
            'email_sent': False
        }
        submissions_collection.insert_one(submission_doc)
        print("Stored in MongoDB successfully")

        # Generate email content using form-specific template
        print(f"Generating email content with form-specific template: {form_config['prompt_template']}")
        email_content = generate_email_content(answers, form_config, webhook_data)
        print(f"Generated content: {email_content[:100]}...")

        # Send email with form-specific subject and sender
        print("Sending email...")
        email_result = send_email(
            to_email=user_email,
            subject=form_config['email_subject'],
            content=email_content,
            submission_id=submission_id,
            from_email=form_config['from_email']
        )

        if email_result:
            print("Email sent successfully!")
            submissions_collection.update_one(
                {'_id': submission_id},
                {'$set': {'email_sent': True, 'email_sent_at': datetime.utcnow()}}
            )

        return jsonify({
            'status': 'success', 
            'submission_id': submission_id,
            'form_id': form_id,
            'form_name': form_config['name']
        }), 200

    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/feedback', methods=['GET'])
def handle_feedback():
    """Handle feedback button clicks"""
    rating = request.args.get('rating')
    submission_id = request.args.get('id')

    if not rating or not submission_id:
        return "Invalid feedback request", 400

    # Store feedback
    feedback_doc = {
        'submission_id': submission_id,
        'rating': rating,
        'created_at': datetime.utcnow()
    }
    feedback_collection.insert_one(feedback_doc)

    # Return a simple thank you page
    return f"""
    <html>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>Thank you for your feedback!</h1>
        <p>Your {'😊' if rating == 'positive' else '😐' if rating == 'neutral' else '☹️'} feedback has been recorded.</p>
    </body>
    </html>
    """

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/forms', methods=['GET'])
def list_supported_forms():
    """List all supported forms"""
    return jsonify({
        'supported_forms': get_supported_forms(),
        'total_forms': len(get_supported_forms())
    }), 200

# Alternative: Polling approach (if webhooks aren't available)
def poll_typeform(form_id, last_token=None):
    """Poll Typeform API for new responses"""
    headers = {
        'Authorization': f'Bearer {os.environ.get("TYPEFORM_API_TOKEN")}'
    }

    params = {}
    if last_token:
        params['after'] = last_token

    response = requests.get(
        f'https://api.typeform.com/forms/{form_id}/responses',
        headers=headers,
        params=params
    )

    if response.status_code == 200:
        return response.json()
    return None

if __name__ == '__main__':
    # For local development
    app.run(debug=True, port=5001)

