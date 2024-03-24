from flask import Flask, render_template, request, jsonify
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_infinite', methods=['POST'])
def start_infinite():
    def infinite_response():
        while True:
            yield '1\n'

    return app.response_class(infinite_response(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
