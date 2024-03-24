from flask import Flask, Response, stream_with_context
import time

app = Flask(__name__)

def generate_numbers():
    count = 1
    while True:
        yield str(count) + '<br/>'
        count += 1
        time.sleep(1)

@app.route('/')
def index():
    return """
    <html>
    <body>
    <h1>Click the button to start counting</h1>
    <button onclick="startCounting()">Start Counting</button>
    <div id="output"></div>
    <script>
        function startCounting() {
            var source = new EventSource('/stream');
            source.onmessage = function(event) {
                document.getElementById("output").innerHTML += event.data;
            };
        }
    </script>
    </body>
    </html>
    """

@app.route('/stream')
def stream():
    def generate():
        count = 1
        while True:
            yield f"data: {count}\n\n"
            count += 1
            time.sleep(1)

    return Response(generate(), mimetype="text/event-stream")


if __name__ == '__main__':
    app.run(debug=True)
