import flask
from owlupdater import read_owl_file

app = flask.Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return flask.render_template('form.html')


@app.route('/', methods=['POST'])
def handle_form():
    print(flask.request.form)
    return wordlist(flask.request.form['url'], flask.request.form['object0'], flask.request.form['object1'])


def wordlist(url, object0, object1):
    results = read_owl_file(url, object0, object1)
    return flask.render_template('wordlist.html', results=results)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5050)
