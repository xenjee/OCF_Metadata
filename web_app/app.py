import os
from flask import Flask, render_template, request, redirect, url_for, flash

# Prepend REDCINE-X PRO directory to PATH so REDline is found.
os.environ['PATH'] = "/Applications/REDCINE-X PRO/REDCINE-X PRO.app/Contents/MacOS:" + os.environ.get('PATH', '')

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def find_files(source_folder, extensions):
    matched_files = []
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if any(file.lower().endswith(ext.lower()) for ext in extensions):
                matched_files.append(os.path.join(root, file))
    return matched_files

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    source_folder = request.form.get('source_folder')
    camera_brand = request.form.get('camera_brand')

    if not source_folder or not os.path.isdir(source_folder):
        flash("Invalid or missing source folder.")
        return redirect(url_for('index'))

    if camera_brand == "ARRI":
        extensions = ['.mxf', '.mov']
    elif camera_brand == "RED":
        extensions = ['.r3d']
    elif camera_brand == "SONY":
        extensions = ['.mxf']
    else:
        extensions = ['.mxf', '.mov', '.r3d']

    found_files = find_files(source_folder, extensions)
    ext_str = ",".join(extensions)
    return render_template('search_results.html',
                           source_folder=source_folder,
                           camera_brand=camera_brand,
                           file_ext=ext_str,
                           found_files=found_files)

@app.route('/generate', methods=['POST'])
def generate():
    source_folder = request.form.get('source_folder')
    camera_brand = request.form.get('camera_brand')
    dest_folder = request.form.get('dest_folder')

    if not source_folder or not os.path.isdir(source_folder):
        flash("Invalid or missing source folder.")
        return redirect(url_for('index'))
    if not dest_folder:
        flash("Invalid or missing destination folder.")
        return redirect(url_for('search'))

    os.makedirs(dest_folder, exist_ok=True)

    if camera_brand == "ARRI":
        extensions = ['.mxf', '.mov']
    elif camera_brand == "RED":
        extensions = ['.r3d']
    elif camera_brand == "SONY":
        extensions = ['.mxf']
    else:
        extensions = ['.mxf', '.mov', '.r3d']

    found_files = find_files(source_folder, extensions)
    generated_files = []
    from scripts.save_json_metadata import SaveJsonMetadata
    for file_path in found_files:
        saver = SaveJsonMetadata(filepath=file_path, camera_brand=camera_brand)
        json_file = saver.save(dest_folder)
        if json_file:
            generated_files.append(json_file)

    return render_template('generate_results.html', generated_files=generated_files)

if __name__ == '__main__':
    app.run(debug=True)
