"""Example of using Forms API."""

from nc_py_api import Nextcloud

# Initialize Nextcloud client
nc = Nextcloud(nextcloud_url="http://nextcloud.local", nc_auth_user="admin", nc_auth_pass="admin")

# Check if Forms API is available
if nc.forms.available:
    # Get all forms
    forms = nc.forms.get_list()
    print(f"Found {len(forms)} forms:")
    for form in forms:
        print(f"  - {form.title} (ID: {form.form_id}, Owner: {form.owner})")

    # Create a new form
    new_form = nc.forms.create(
        title="Customer Feedback Survey",
        description="Please provide your feedback",
        is_anonymous=True,
        submit_multiple=False,
    )
    print(f"\nCreated form: {new_form.title} (ID: {new_form.form_id})")

    # Add a question to the form
    question = nc.forms.create_question(
        form_id=new_form.form_id,
        question_type="short",
        text="What is your overall satisfaction?",
        is_required=True,
        order=1,
    )
    print(f"Added question: {question.text} (ID: {question.question_id})")

    # Add a multiple choice question
    mc_question = nc.forms.create_question(
        form_id=new_form.form_id,
        question_type="multiple_choice",
        text="Which feature do you like most?",
        options=["Feature A", "Feature B", "Feature C"],
        is_required=True,
        order=2,
    )
    print(f"Added multiple choice question: {mc_question.text}")

    # Get all questions for the form
    questions = nc.forms.get_questions(new_form.form_id)
    print(f"\nForm has {len(questions)} questions")

    # Submit a response
    submission = nc.forms.create_submission(
        form_id=new_form.form_id,
        answers=[
            {"questionId": question.question_id, "text": "Very satisfied"},
            {"questionId": mc_question.question_id, "text": "Feature A"},
        ],
    )
    print(f"\nCreated submission (ID: {submission.submission_id})")

    # Get all submissions
    submissions = nc.forms.get_submissions(new_form.form_id)
    print(f"Form has {len(submissions)} submissions")

    # Get form details
    form_details = nc.forms.get(new_form.form_id)
    print(f"\nForm details: {form_details.title} - {form_details.description}")
else:
    print("Forms API is not available on this Nextcloud instance.")
