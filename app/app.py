import base64
from flask import Flask, flash, render_template, request, redirect, session
from config import Config
from models import db
from models import User, Note
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import boto3
import io
from datetime import datetime
from utils import summarize_notes
import markdown

load_dotenv()
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_S3_REGION")
)
bucket_name = os.getenv("AWS_S3_BUCKET_NAME")


app = Flask(__name__)
app.config.from_object(Config)

# Required for sessions to work
app.secret_key = app.config['SECRET_KEY']

# Initialize the database
db.init_app(app)

@app.route('/db_test_select')
def db_test_select():
    users = User.query.all()
    return [f"{user.name}, {user.email}" for user in users]

@app.route('/db_test_clear')
def db_test_clear():
    User.query.delete()
    db.session.commit()
    return "Cleared all users"

@app.route('/')
def landing():
    return render_template('landing_page.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("Handling signup request")

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(name, email, password)

        # if User.query.filter_by(email=email).first():
        #     flash("Email already registered. Please log in.")
        #     return redirect('/signup')

        hashed_password = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        print("User created successfully") 

        session['user_id'] = user.id
        session['user_name'] = user.name

        return redirect('/dashboard')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login') 


@app.route('/dashboard')
def dashboard():
    if 'user_name' not in session:
        return redirect('/signup')
    return render_template('dashboard.html', user_name=session['user_name'])

@app.route('/process', methods=['POST'])
def process_note():
    note_text = request.form.get('noteText')
    file = request.files.get('noteFile')
    note_received, file_received = False, False
    txt_input, file_input = note_text, ''

    if not file and not note_text.strip():
        flash("Please upload a file or paste some notes.")
        return redirect('/dashboard')

    if note_text and note_text.strip():  # User uploaded in text-field
        note_recieved = True
        print("Received text input:", note_text)

        filename = f"{session['user_name']}/text_notes/{datetime.now().isoformat()}.txt"
        file_obj = io.BytesIO(note_text.encode('utf-8'))
        s3.upload_fileobj(file_obj, bucket_name, filename)

        print(f"Uploaded Text as {filename}")

    if file and file.filename:  # User uploaded a file
        file_recieved = True
        print("Received file:", file.filename)

        file_bytes = file.read()
        file.seek(0)

        file_base64 = base64.b64encode(file_bytes).decode('utf-8')
        file_input = file_base64

        filename = f"{session['user_name']}/file_notes/{file.filename}"
        s3.upload_fileobj(io.BytesIO(file_bytes), bucket_name, filename)
 
        print(f"Uploaded File as {filename}")
    
    if note_received or file_received:
        session['txt_input'] = txt_input
        session['file_input'] = file_input
        return render_template('processing.html')

    return render_template('dashboard.html', user_name=session['user_name'])

@app.route('/generate_summary')
def generate_summary():
    txt_input = session.get('txt_input')
    file_input = session.get('file_input')
    summarized = summarize_notes(txt_input, file_input)
    session['summary'] = summarized
    return redirect('/summary')  


@app.route('/summary')
def summary():
    summary_text = session.get('summary', 'No summary available.')
    summary_text = markdown.markdown(summary_text)
    return render_template('summary.html', summary=summary_text)


# One-time command to create the database
@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database tables created.")


if __name__ == '__main__':
    app.run(debug=True, reloader=True)
