from flask import Flask, Response, render_template, request, jsonify

## Add required imports
from azure.storage.blob import BlobServiceClient, ContentSettings
from datetime import datetime
import os
from flask_cors import CORS

STORAGE_ACCOUNT_URL = os.getenv("STORAGE_ACCOUNT_URL")
IMAGES_CONTAINER = os.getenv("IMAGES_CONTAINER", "lanternfly-images")
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

bsc = BlobServiceClient.from_connection_string(os.environ["AZURE_STORAGE_CONNECTION_STRING"])
cc  = bsc.get_container_client(os.getenv("IMAGES_CONTAINER", "lanternfly-images")) # Replace with Container name cc.url will get you the url path to the container.  
app = Flask(__name__)
CORS(app)

@app.post("/api/v1/upload")
def upload():
    try:
        f = request.files["file"]
        if not f:
            return jsonify(error="No file uploaded"), 400

        # Accept only image/* content types
        if not f.mimetype.startswith("image/"):
            return jsonify(error="Invalid file type. Only images allowed."), 415

        img_bytes = f.read()
        filename = f.filename
        img_blob = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}-{filename}"
        img_bc = bsc.get_blob_client("lanternfly-images", img_blob)
        img_bc.upload_blob(
            img_bytes,
            overwrite=True,
            content_settings=ContentSettings(content_type=f.mimetype)
        )
        return jsonify(ok=True, url=f"{cc.url}/{img_blob}")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.route("/api/v1/health", methods=["GET"])
def health():
  return {"ok":True}
@app.route("/api/v1/gallery", methods=["GET"])
def gallery():
    try:
        gallery = [f"{cc.url}/{b.name}" for b in cc.list_blobs()]
        return jsonify(ok=True, gallery=gallery)
    except Exception as e:
        return jsonify(urls=[], error=str(e)), 500
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))