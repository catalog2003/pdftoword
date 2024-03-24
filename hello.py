from flask import Flask, request, send_file, jsonify
from pdf2docx import Converter
import os
import threading
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app)

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

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF to Word Converter</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f0f0f0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .converter {
                max-width: 400px;
                width: 100%;
                padding: 20px;
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            h1 {
                font-size: 24px;
                margin-bottom: 20px;
                color: #333;
            }
            .file-upload {
                padding: 10px 20px;
                background-color: #007bff;
                color: #fff;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s;
            }
            .file-upload:hover {
                background-color: #0056b3;
            }
            #file-input {
                display: none;
            }
            #loading {
                display: none;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 10;
            }
            #download-link {
                display: none;
                padding: 10px 20px;
                background-color: #28a745;
                color: #fff;
                border: none;
                border-radius: 5px;
                text-decoration: none;
                transition: background-color 0.3s;
            }
            #download-link:hover {
                background-color: #218838;
            }
            .success-message {
                display: none;
                color: #28a745;
                font-size: 18px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
    
    <div class="converter">
        <h1>PDF to Word Converter</h1>
        <label for="file-input" class="file-upload"><i class="fas fa-file-upload"></i> Choose PDF File</label>
        <input id="file-input" type="file" name="file" accept=".pdf" onchange="convertPdfToWord()">
        <div id="loading"><i class="fas fa-spinner fa-spin"></i> Converting...</div>
    </br>
    </br>
        <a id="download-link" href="#" download><i class="fas fa-download"></i> Download Converted File</a>
        <div class="success-message" id="success-message">Conversion successful!</div>
    </div>
    
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
        function convertPdfToWord() {
            var fileInput = document.getElementById('file-input');
            var file = fileInput.files[0];
    
            if (!file || !file.name.endsWith('.pdf')) {
                alert('Please select a PDF file.');
                return;
            }
    
            var formData = new FormData();
            formData.append('file', file);
    
            $('#loading').show();
    
            $.ajax({
                url: '/convert',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function (data) {
                    checkConversionStatus(data.output_docx);
                },
                error: function (error) {
                    console.log(error);
                    $('#loading').hide();
                }
            });
        }
    
        function checkConversionStatus(outputDocx) {
            var interval = setInterval(function () {
                $.ajax({
                    url: '/status/' + outputDocx,
                    type: 'GET',
                    success: function (status) {
                        if (status.status === 'complete') {
                            clearInterval(interval);
                            $('#loading').hide();
                            $('#download-link').attr('href', '/download/' + outputDocx);
                            $('#download-link').show();
                            $('#success-message').show();
                        }
                    },
                    error: function (error) {
                        console.log(error);
                        clearInterval(interval);
                        $('#loading').hide();
                    }
                });
            }, 1000);
        }
    </script>
    
    </body>
   
 </html>
    </body>
    </html>
    """

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)