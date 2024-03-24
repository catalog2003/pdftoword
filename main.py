from flask import Flask, request, send_file, jsonify
from pdf2docx import Converter
import os
import threading
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/convert": {"origins": "http://127.0.0.1:5500"}})

conversion_threads = {}

def convert_with_progress(pdf_path, output_docx):
    cv = Converter(pdf_path)
    cv.convert(output_docx, start=0, end=None)
    cv.close()

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"})

    pdf_file = request.files['file']

    if pdf_file.filename == '':
        return jsonify({"error": "No selected file"})

    # Save the uploaded PDF file
    pdf_path = os.path.join('uploads', pdf_file.filename)
    pdf_file.save(pdf_path)

    # Convert PDF to Word
    output_docx = f"converted_{os.path.splitext(pdf_file.filename)[0]}.docx"

    # Start the conversion process in a separate thread
    conversion_thread = threading.Thread(target=convert_with_progress, args=(pdf_path, output_docx))
    conversion_threads[output_docx] = conversion_thread
    conversion_thread.start()

    # Provide the converted Word file name for download
    return jsonify({"output_docx": output_docx})

@app.route('/status/<filename>')
def status(filename):
    if filename in conversion_threads and not conversion_threads[filename].is_alive():
        return jsonify({"status": "complete"})
    else:
        return jsonify({"status": "in_progress"})

@app.route('/download/<filename>')
def download(filename):
    # Fix the path format issue on Windows
    filename = filename.replace('"', '')
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
