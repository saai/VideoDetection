#encoding=utf-8
import os
import uuid

from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from distutils.dir_util import mkpath
from werkzeug import secure_filename
from celery import Celery

import subprocess as sp

app = Flask(__name__)
job_queue = Celery('tasks',backend='redis://localhost',broker='redis://localhost//')

app.config['UPLOAD_FOLDER'] = 'uploads/'
mkpath('uploads/')

# for Linux / Mac
FFMPEG_BIN = "ffmpeg"

# get frames from movie
def get_frames(filename, output_dir):
    command = [ FFMPEG_BIN,
        '-i', filename,
        '-r', '0.5',
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

# save files -> get_fames-> process_images()
# return processed image url json
@app.route('/upload', methods=['POST']) 
def upload():
    file = request.files['file']
    if file and allowed_file(file.filename):
        task_id = generate_task()
        filename = secure_filename(file.filename)
        filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filename)
        get_frames(filename, 'tasks/' + task_id + '/frames')
        task_path = os.path.abspath('tasks/' + task_id)
        detect_job(os.path.join(task_path, 'frames'), os.path.join(task_path, 'results')) 
        return 'OK ' + task_id

def detect_job(frames_dir, result_dir):
    files = os.listdir(frames_dir) 
    for fname in files:
        in_file = os.path.join(frames_dir, fname)
        out_file = os.path.join(result_dir, fname)
    job_queue.send_task('detect_img', [in_file, out_file])

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int("8066"),
        debug=True
    )

