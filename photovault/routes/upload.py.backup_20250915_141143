import os, uuid

def secure_filename(filename):
    # Use Werkzeug's secure_filename or similar
    from werkzeug.utils import secure_filename
    return secure_filename(filename)

def handle_upload(file):
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1]
    random_name = f"{uuid.uuid4().hex}{ext}"
    file.save(os.path.join(upload_folder, random_name))