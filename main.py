import os
from flask import Flask, request, jsonify, render_template
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['JWT_SECRET_KEY'] = 'jwtsecretkey'  # Secret key for JWT
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize JWT
jwt = JWTManager(app)

# Define max size limits per file type (in MB)
FILE_SIZE_LIMITS = {
    'image': 5 * 1024 * 1024,  # 5MB
    'pdf': 4 * 1024 * 1024,    # 4MB
    'doc': 4 * 1024 * 1024,    # 4MB
    'video': 20 * 1024 * 1024  # 20MB
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'jpg','jpeg','png','pdf', 'doc','docx', 'mp4','mkv'}

class UploadFileForm(FlaskForm):
    file = FileField("Choose a file")
    submit = SubmitField("Upload")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_category(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in ['jpg', 'jpeg', 'png', 'gif']:
        return 'image'
    elif ext in ['pdf']:
        return 'pdf'
    elif ext in ['doc', 'docx']:
        return 'doc'
    elif ext in ['mp4', 'avi', 'mkv']:
        return 'video'
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@jwt_required() 
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    file_category = get_file_category(file.filename)
    if not file_category:
        return jsonify({'error': 'Unsupported file format'}), 400

    max_size = FILE_SIZE_LIMITS[file_category]

    file.seek(0, os.SEEK_END)
    file_size = file.tell()  # Get file size
    file.seek(0)  

    if file_size > max_size:
        return jsonify({'error': f'File exceeds max size for {file_category}'}), 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return jsonify({'message': f'File {filename} uploaded successfully!'}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == 'admin' and password == 'password':
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200

    return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(debug=True)
