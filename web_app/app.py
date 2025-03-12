from flask import Flask, render_template, request, redirect, url_for, flash
import os
from scripts.save_json_metadata import SaveJsonMetadata

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # needed for flashing messages

def find_files(source_folder, file_ext):
    """
    Recursively search source_folder for files that end with the given file_ext.
    """
    matched_files = []
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.lower().endswith(file_ext.lower()):
                matched_files.append(os.path.join(root, file))
    return matched_files

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    source_folder = request.form.get('source_folder')
    file_ext = request.form.get('file_ext')
    
    if not os.path.isdir(source_folder):
        flash("Source folder does not exist.")
        return redirect(url_for('index'))
    
    found_files = find_files(source_folder, file_ext)
    return render_template('search_results.html', source_folder=source_folder, file_ext=file_ext, found_files=found_files)

@app.route('/generate', methods=['POST'])
def generate():
    source_folder = request.form.get('source_folder')
    file_ext = request.form.get('file_ext')
    dest_folder = request.form.get('dest_folder')
    
    if not os.path.isdir(dest_folder):
        flash("Destination folder does not exist.")
        return redirect(url_for('index'))
    
    # Re-find the files (or alternatively, pass the list from the previous step)
    found_files = find_files(source_folder, file_ext)
    generated_files = []
    for file_path in found_files:
        saver = SaveJsonMetadata(filepath=file_path)
        json_file = saver.save(dest_folder)
        generated_files.append(json_file)
    
    return render_template('generate_results.html', generated_files=generated_files)

if __name__ == '__main__':
    app.run(debug=True)
