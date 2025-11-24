import os
import time
import zipfile
from flask import (
    Flask, render_template, request,
    redirect, url_for, send_from_directory, flash
)
from werkzeug.utils import secure_filename
from PIL import Image, PngImagePlugin
import piexif

# ------------ Config ------------

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
CHALLENGE_FOLDER = os.path.join(BASE_DIR, "challenges")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHALLENGE_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["CHALLENGE_FOLDER"] = CHALLENGE_FOLDER
app.secret_key = "change-this-secret-key"  # needed for flash messages


# ------------ Helpers ------------

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_search_prefix(flag: str) -> str:
    # For grep commands: "flag{xxx}" -> "flag"
    return flag.split("{")[0] if "{" in flag else flag


# ------------ Stego Methods ------------

def metadata_stego(input_path: str, flag: str) -> tuple[str, str]:
    """Embed flag into EXIF UserComment (JPEG only)."""
    img = Image.open(input_path)
    img_format = img.format.upper()

    if img_format not in ["JPEG", "JPG"]:
        raise ValueError("Metadata method only supports JPEG/JPG images.")

    try:
        exif_dict = piexif.load(img.info.get("exif", b""))
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    user_comment = flag.encode("utf-8")
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = user_comment

    exif_bytes = piexif.dump(exif_dict)

    output_name = f"challenge_metadata_{int(time.time())}.jpg"
    output_path = os.path.join(CHALLENGE_FOLDER, output_name)

    img.save(output_path, exif=exif_bytes)

    hint = f"exiftool {output_name} | grep {extract_search_prefix(flag)}"
    return output_name, hint


def strings_stego(input_path: str, flag: str) -> tuple[str, str]:
    """Append flag as raw bytes so it’s visible via strings + grep."""
    with open(input_path, "rb") as f:
        data = f.read()

    marker = b"CTF_FLAG_START:" + flag.encode() + b":CTF_FLAG_END"
    new_data = data + marker

    ext = os.path.splitext(input_path)[1].lower()
    output_name = f"challenge_strings_{int(time.time())}{ext}"
    output_path = os.path.join(CHALLENGE_FOLDER, output_name)

    with open(output_path, "wb") as f:
        f.write(new_data)

    hint = f"strings {output_name} | grep {extract_search_prefix(flag)}"
    return output_name, hint


def zip_stego(input_path: str, flag: str) -> tuple[str, str]:
    """
    Append a ZIP containing flag.txt to the end of the image.
    Extractable via binwalk -e.
    """
    temp_zip = os.path.join(CHALLENGE_FOLDER, "temp_flag.zip")

    with zipfile.ZipFile(temp_zip, "w") as zipf:
        zipf.writestr("flag.txt", flag)

    with open(input_path, "rb") as f:
        img_data = f.read()
    with open(temp_zip, "rb") as zf:
        zip_data = zf.read()

    output_name = f"challenge_zip_{int(time.time())}.png"
    output_path = os.path.join(CHALLENGE_FOLDER, output_name)

    with open(output_path, "wb") as out:
        out.write(img_data + zip_data)

    os.remove(temp_zip)

    hint = f"binwalk -e {output_name} && cat _{output_name}.extracted/flag.txt"
    return output_name, hint


def zsteg_stego(input_path: str, flag: str) -> tuple[str, str]:
    """
    Embed flag into PNG tEXt chunk.
    Detectable via zsteg.
    """
    img = Image.open(input_path)
    img_format = img.format.upper()

    if img_format != "PNG":
        raise ValueError("ZSteg method only supports PNG images.")

    meta = PngImagePlugin.PngInfo()
    meta.add_text("Flag", flag)

    output_name = f"challenge_zsteg_{int(time.time())}.png"
    output_path = os.path.join(CHALLENGE_FOLDER, output_name)
    img.save(output_path, pnginfo=meta)

    hint = f"zsteg {output_name}"
    return output_name, hint


METHODS = {
    "metadata": {
        "label": "EXIF Metadata (JPEG only)",
        "func": metadata_stego,
        "note": "Uses exiftool to recover the flag.",
    },
    "strings": {
        "label": "Binary Strings (JPG/PNG)",
        "func": strings_stego,
        "note": "Uses strings + grep to recover the flag.",
    },
    "zip": {
        "label": "Hidden ZIP (binwalk)",
        "func": zip_stego,
        "note": "Uses binwalk -e to extract flag.txt.",
    },
    "zsteg": {
        "label": "PNG Chunk Stego (zsteg, PNG only)",
        "func": zsteg_stego,
        "note": "Uses zsteg to find the flag in PNG text chunks.",
    },
}


# ------------ Routes ------------

@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        methods=METHODS,
        result=None,
    )


@app.route("/generate", methods=["POST"])
def generate():
    if "image" not in request.files:
        flash("No file part in request.", "error")
        return redirect(url_for("index"))

    file = request.files["image"]
    flag = request.form.get("flag", "").strip()
    method_key = request.form.get("method")

    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    if not flag:
        flash("Flag cannot be empty.", "error")
        return redirect(url_for("index"))

    if method_key not in METHODS:
        flash("Invalid method selected.", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Invalid file type. Use PNG/JPG/JPEG.", "error")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(upload_path)

    method = METHODS[method_key]

    try:
        output_name, extraction_hint = method["func"](upload_path, flag)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Error generating challenge: {e}", "error")
        return redirect(url_for("index"))

    result = {
        "output_name": output_name,
        "extraction_hint": extraction_hint,
        "method_label": method["label"],
        "method_note": method["note"],
    }

    return render_template(
        "index.html",
        methods=METHODS,
        result=result,
    )


@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(
        app.config["CHALLENGE_FOLDER"],
        filename,
        as_attachment=True,
    )


if __name__ == "__main__":
    # Run locally
    app.run(host="127.0.0.1", port=5000, debug=True)
