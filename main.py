#encoding=utf-8
import os
import uuid

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import subprocess as sp
from distutils.dir_util import mkpath

from werkzeug import secure_filename

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads/'

# for Linux / Mac
FFMPEG_BIN = "ffmpeg"

# get frames from movie
def get_frames(filename, output_dir):
    command = [ FFMPEG_BIN,
        '-i', filename,
        '-r', '1',
        '-q:v', '2',
        '-f', 'image2',
        output_dir + '/frames-%d.jpeg'
    ]
    pipe = sp.Popen(command, stderr=sp.PIPE)
    pipe.communicate()

@app.route('/')
def index():
    return render_template('index.html')

# for given filename, return wheather it's an allowed type or not
# for debugging, we always return true.
def allowed_file(filename):
    return True

def generate_task():
    task_id = str(uuid.uuid1())
    mkpath('tasks/' + task_id)
    mkpath('tasks/' + task_id + '/frames')
    return task_id

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file and allowed_file(file.filename):
        task_id = generate_task()
        filename = secure_filename(file.filename)
        filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filename)
        get_frames(filename, 'tasks/' + task_id + '/frames')
        return 'OK ' + task_id

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int("8066"),
        debug=True
    )

