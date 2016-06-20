import flask
import pickle
import redis
import hashlib
from owlupdater import read_owl_file

app = flask.Flask(__name__)
redis_server = redis.StrictRedis(host='localhost', port=6379, db=0)

@app.route('/', methods=['GET'])
def index():
    return flask.render_template('form.html')

@app.route('/', methods=['POST'])
def handle_form():
    return check_hash(flask.request.form['url'],
            [flask.request.form['uri0'],
            flask.request.form['uri1'],
            flask.request.form['uri2'],
            flask.request.form['uri3'],
            flask.request.form['uri4']])

@app.route('/<string:sha>', methods=['GET'])
def get_hash(sha=''):
    if not sha:
       return flask.redirect(flask.url_for('index')) 
    return flask.render_template('loading.html')

@app.route('/<string:sha>/data', methods=['GET'])
def load_data(sha=''):
    if not sha:
       return flask.redirect(flask.url_for('index')) 
    raw = redis_server.get(sha)
    search = pickle.loads(raw)
    return wordlist(search['url'], search['annotations'])

def check_hash(url, annotations):
    sha_string = url + '.'.join(annotations)
    sha = hashlib.sha256(sha_string.encode('utf-8')).hexdigest()[:8]
    if not redis_server.exists(sha):
        redis_server.set(sha, pickle.dumps({'url': url, 'annotations': annotations}))
    return flask.redirect(flask.url_for('get_hash', sha=sha))

def wordlist(url, annotations):
    print(annotations)
    uris = []
    for annotation in annotations:
        if annotation:
            uris.append(annotation)
    results = read_owl_file(url, uris)
    return flask.render_template('wordlist.html', results=results)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5050)
