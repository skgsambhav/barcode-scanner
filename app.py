from flask import Flask, render_template, request, jsonify
import os, requests

app = Flask(__name__)
# Set this in your environment:  set CLOUDMERSIVE_API_KEY=your_key_here
API_KEY = os.getenv("CLOUDMERSIVE_API_KEY", "")

@app.route("/")
def index():
    return render_template("scan.html")

@app.route("/api/decode", methods=["POST"])
def decode():
    if not API_KEY:
        return jsonify({"ok": False, "error": "Missing CLOUDMERSIVE_API_KEY"}), 500

    file = request.files.get("image")
    if not file:
        return jsonify({"ok": False, "error": "No image provided"}), 400

    try:
        # Cloudmersive Barcode Scan: image -> value(s)
        # Endpoint docs: Barcode scan from image (multipart 'imageFile')
        url = "https://api.cloudmersive.com/barcode/scan/image"
        headers = {"Apikey": API_KEY}
        files = {"imageFile": (file.filename or "frame.jpg", file.stream, file.mimetype or "image/jpeg")}
        r = requests.post(url, headers=headers, files=files, timeout=30)
        r.raise_for_status()
        data = r.json()
        # Cloudmersive returns list of FoundBarcodes, each with 'BarcodeType' and 'RawText'
        results = []
        for item in (data.get("FoundBarcodes") or []):
            results.append({
                "type": item.get("BarcodeType"),
                "text": item.get("RawText")
            })
        return jsonify({"ok": True, "results": results})
    except requests.HTTPError as e:
        return jsonify({"ok": False, "error": f"Cloudmersive HTTP {e.response.status_code}", "details": e.response.text[:400]}), 502
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Run:  python app.py   (Use HTTPS in prod)
    app.run(host="0.0.0.0", port=5000, debug=True)
