import flask
import pickle
import redis
import hashlib
from owlupdater import read_owl_file
from flask import jsonify, Response
import werkzeug
import io
import csv

app = flask.Flask(__name__)
redis_server = redis.StrictRedis(host='localhost', port=6379, db=0)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

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
            flask.request.form['uri4']],
            'uri' in flask.request.form.keys())

@app.route('/<string:sha>', methods=['GET'])
def get_hash(sha=''):
    if not sha:
       return flask.redirect(flask.url_for('index'))
    loading = not redis_server.exists(sha + '/data')
    return flask.render_template('loading.html', loading=loading)

@app.route('/<string:sha>/refresh', methods=['GET'])
def refresh_data(sha=''):
    if not sha:
       return flask.redirect(flask.url_for('index'))
    redis_server.delete(sha + '/data')
    return flask.redirect(flask.url_for('get_hash', sha=sha))

@app.route('/<string:sha>/data', methods=['GET'])
def load_data(sha=''):
    if not sha:
       return flask.redirect(flask.url_for('index'))
    raw = redis_server.get(sha)
    search = pickle.loads(raw)
    uri = False
    if 'uri' in search.keys():
        uri = search['uri']
    results = wordlist(search['url'], search['annotations'], uri)
    return flask.render_template('wordlist.html', results=results)

@app.route('/<string:sha>/json', methods=['GET'])
def load_json(sha=''):
    if not sha:
       return flask.redirect(flask.url_for('index'))
    raw = redis_server.get(sha)
    search = pickle.loads(raw)
    uri = False
    if 'uri' in search.keys():
        uri = search['uri']
    return flask.jsonify(wordlist(search['url'], search['annotations'], uri))

@app.route('/<string:sha>/csv', methods=['GET'])
def load_csv(sha=''):
    if not sha:
       return flask.redirect(flask.url_for('index'))
    raw = redis_server.get(sha)
    search = pickle.loads(raw)
    uri = False
    if 'uri' in search.keys():
        uri = search['uri']
    results = wordlist(search['url'], search['annotations'], uri)
    csv_file = io.StringIO()
    csv_writer = csv.writer(csv_file, dialect='excel')
    csv_writer.writerow(['term'] + results['labels'])
    for row in results['results']:
        nrow = []
        nrow.append(row['term'])
        for label in results['labels']:
            nrow.append(str(row[label]))
        csv_writer.writerow(nrow)
    headers = werkzeug.datastructures.Headers()
    headers.add('Content-Type', 'text/csv')
    headers.add('Content-Disposition', 'attachment', filename='{}.csv'.format(sha))
    output = csv_file.getvalue()
    csv_file.close()
    return Response(output, mimetype='text/csv', headers=headers)


def check_hash(url, annotations, uri):
    sha = get_sha(url, annotations, uri)
    if not redis_server.exists(sha):
        redis_server.set(sha, pickle.dumps({'url': url,
                                            'annotations': annotations,
                                            'uri': uri}))
    return flask.redirect(flask.url_for('get_hash', sha=sha))

def wordlist(url, annotations, uri):
    sha = get_sha(url, annotations, uri)
    if redis_server.exists(sha + '/data'):
        raw = redis_server.get(sha + '/data')
        results = pickle.loads(raw)
    else:
        uris = []
        for annotation in annotations:
            if annotation:
                uris.append(annotation)
        try:
            results = read_owl_file(url, uris)
            redis_server.set(sha + '/data', pickle.dumps(results))
            redis_server.expire(sha + '/data', 86400)
        except IOError as e:
            raise InvalidUsage("Unable to load OWL file", status_code=500)
    results['sha'] = sha
    results['uri'] = uri
    return results

def get_sha(url, annotations, uri):
    sha_string = url + '.'.join(annotations)
    if uri:
        sha_string += 'uri'
    return hashlib.sha256(sha_string.encode('utf-8')).hexdigest()[:8]


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5050)
