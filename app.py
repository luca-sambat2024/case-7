from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from azure.storage.blob import BlobServiceClient, ContentSettings
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

def get_container_client():
    conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container = os.getenv("IMAGES_CONTAINER", "lanternfly-images")
    bsc = BlobServiceClient.from_connection_string(conn)
    return bsc.get_container_client(container)

@app.post("/api/v1/upload")
def upload():
    try:
        f = request.files.get("file")
        if not f:
            return jsonify(error="No file uploaded"), 400
        if not f.mimetype.startswith("image/"):
            return jsonify(error="Invalid file type. Only images allowed."), 415

        img_bytes = f.read()
        filename = f"{datetime.utcnow():%Y%m%dT%H%M%S}-{f.filename}"
        cc = get_container_client()
        bc = cc.get_blob_client(filename)
        bc.upload_blob(img_bytes, overwrite=True, content_settings=ContentSettings(content_type=f.mimetype))
        return jsonify(ok=True, url=f"{cc.url}/{filename}")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.get("/api/v1/health")
def health():
    return {"ok": True}

@app.get("/api/v1/gallery")
def gallery():
    try:
        cc = get_container_client()
        gallery = [f"{cc.url}/{b.name}" for b in cc.list_blobs()]
        return jsonify(ok=True, gallery=gallery)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.get("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
