
# 🔍 ForensiX — Automated Steganography Challenge Generator

ForensiX is a cybersecurity tool designed to help **CTF challenge creators** automatically hide flags inside images using multiple steganography and digital forensics techniques. Each generated challenge includes the **exact extraction command**, enabling realistic and educational forensics training.

---

## 🚀 Features

| Method | Supported Formats | Tool Required for Extraction | Skill Tested |
|--------|-----------------|-----------------------------|--------------|
| Metadata Stego | JPG/JPEG | `exiftool` | EXIF forensics |
| Binary Strings Stego | JPG/PNG | `strings + grep` | Memory / binary text carving |
| Hidden ZIP Stego | JPG/PNG | `binwalk -e` | File structure & carving |
| PNG Chunk Stego | PNG only | `zsteg` | True steganography |

---

## 🧪 Demo Web Application

Upload an image → enter a flag → select a method → generate the challenge → download the modified file.
<img width="952" height="707" alt="Screenshot From 2025-11-24 18-58-23" src="https://github.com/user-attachments/assets/26ce2f68-bdb0-46d1-bb3f-79a14c0b0040" />

Run locally:
```bash
python3 app.py<img width="963" height="794" alt="Screenshot From 2025-11-24 18-59-19" src="https://github.com/user-attachments/assets/240ae930-fb72-4736-aec3-cfcba48f12f9" />

````

Access the app:

```
http://127.0.0.1:5000/
```

---

## 🌍 Temporary Public Hosting (Safe Demo)

Expose your local app using ngrok:

```bash
ngrok http 5000
```

Share the generated **HTTPS** link with anyone for testing.

---

## 🖥️ CLI Usage

Metadata Stego:

```bash
python3 ctfgen.py --input img.jpg --flag "flag{secret}" --method metadata
exiftool challenge_metadata_*.jpg | grep flag
```

Strings Stego:

```bash
python3 ctfgen.py --input img.png --flag "flag{secret}" --method strings
strings challenge_strings_*.png | grep flag
```

ZIP Stego:

```bash
python3 ctfgen.py --input img.jpg --flag "flag{secret}" --method zip
binwalk -e challenge_zip_*.png
cat _challenge_zip_*/flag.txt
```

ZSteg Stego (PNG only):

```bash
python3 ctfgen.py --input img.png --flag "flag{secret}" --method zsteg
zsteg challenge_zsteg_*.png
```

---

## 📁 Project Structure

```
ctfgen_web/
├─ app.py
├─ ctfgen.py
├─ uploads/
├─ challenges/
├─ templates/
│   └─ index.html
└─ README.md
```

---

## 🧠 Skills Demonstrated

✔ Steganography techniques
✔ Digital forensics analysis
✔ Python secure file handling
✔ Web security principles
✔ Challenge engineering for CTFs

---

## 🔐 Security Notes

⚠ For public hosting:

* Restrict file size
* Validate file types strictly
* Disable `binwalk` & `zsteg` methods

(Local hosting is safest for demos.)

---

## 🔮 Future Improvements

* Steghide (password-based stego)
* Advanced LSB modifications
* Audio & PDF steganography support
* Docker container deployment
* User authentication for hosted version

---

## 👤 Author

**Siro**
Cybersecurity Engineering Student
CTF Player | Forensics Learner

