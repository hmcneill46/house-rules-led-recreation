from flask import Flask, render_template

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    # 0.0.0.0 so other devices on your LAN can reach it
    app.run(host="0.0.0.0", port=5001, debug=True)
