from flask import Flask, request, flash, redirect, send_file, url_for, abort
from markupsafe import escape
from hashlib import sha1
from werkzeug.utils import secure_filename
import yaml
import json
import os
import io

config_paths = ["/etc/chatcdn/", "./"]
config_path = ""

for path in config_paths:
    if os.path.exists(path + "config.yml"):
        config_path = path
        break


if config_path == "" or not os.path.exists(config_path + "config.yml"):
    raise FileNotFoundError("No configuration file was found. Please create one by copying config.yml.example.")

config = yaml.safe_load(open(config_path + "config.yml"))

app = Flask(__name__)

UPLOAD_FOLDER = config["UPLOAD_FOLDER"]
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if config["secret_key"] == "":
    raise ValueError("Please set secret_key within config.yml.")

app.secret_key = config["secret_key"]

def file_hash(filename):
    h = sha1()

    with open(filename, "rb") as file:

        chunk = 0
        while chunk != b"":
            chunk = file.read(1024)
            h.update(chunk)

        return h.hexdigest()

@app.route("/media/<id>")
def redirect_downloads(id):
    filename = os.path.join(UPLOAD_FOLDER, secure_filename(id)) + "-meta.json"

    with open(filename, "r") as metafile:
        if not metafile:
            abort(404)

        metadata = json.loads(metafile.read())

        return redirect(f"/media/{id}/{metadata['filename']}")

@app.route("/media/<id>/<fname>")
def download(id, fname):
    filename = os.path.join(UPLOAD_FOLDER, secure_filename(id))

    if not os.path.exists(filename):
        abort(404)

    with open(filename, "rb") as file:
        if not file:
            abort(404)
        with open(filename + "-meta.json", "r") as metafile:
            metadata = json.loads(metafile.read())
            return send_file(
                    io.BytesIO(file.read()),
                    attachment_filename=metadata["filename"],
                    mimetype=metadata["mimetype"])

@app.route("/cdn/upload", methods=["POST"])
def upload():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if "file" not in request.files:
        abort(404)

    ret_data = { "urls": [] }
    for file in request.files.getlist("file"):
        
        if file.filename == "":
            abort(404)

        file_path = os.path.join(UPLOAD_FOLDER, "tmp")

        file.save(file_path)

        new_name = file_hash(file_path)
        new_path = os.path.join(UPLOAD_FOLDER, new_name)

        os.rename(file_path, new_path)

        ret_data["urls"].append(f"{request.host_url}media/{new_name}")

        metadata = {
            "filename": secure_filename(file.filename),
            "mimetype": file.content_type
        }

        with open(new_path + "-meta.json", "w") as metafile:
            metafile.write(json.dumps(metadata))
        
    return json.dumps(ret_data)
