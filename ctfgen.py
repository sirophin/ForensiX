import os
import time
import zipfile
import argparse
from PIL import Image, PngImagePlugin
import piexif

# Supported stego methods
def insert_metadata(input_image, flag):
    """Embed flag in EXIF metadata (JPEG only)."""
    img = Image.open(input_image)
    img_format = img.format.upper()

    if img_format not in ["JPEG", "JPG"]:
        raise ValueError("Metadata method only works on JPEG images.")

    try:
        exif_dict = piexif.load(img.info.get("exif", b""))
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    user_comment = flag.encode("utf-8")
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = user_comment

    exif_bytes = piexif.dump(exif_dict)
    output_name = f"challenge_metadata_{int(time.time())}.jpg"
    Image.open(input_image).save(output_name, exif=exif_bytes)

    print(f"[+] Challenge Created: {output_name}")
    print(f"[+] Extract using: exiftool {output_name} | grep flag")


def insert_strings(input_image, flag):
    """Append flag text for extraction with `strings`."""
    with open(input_image, "rb") as f:
        data = f.read()

    marker = b"CTF_FLAG_START:" + flag.encode() + b":CTF_FLAG_END"
    new_data = data + marker

    ext = os.path.splitext(input_image)[1]
    output_name = f"challenge_strings_{int(time.time())}{ext}"

    with open(output_name, "wb") as f:
        f.write(new_data)

    print(f"[+] Challenge Created: {output_name}")
    print(f"[+] Extract using: strings {output_name} | grep flag")


def insert_zip(input_image, flag):
    """Hide a ZIP archive containing flag.txt inside the image."""
    temp_zip = "temp_flag.zip"

    with zipfile.ZipFile(temp_zip, "w") as zipf:
        zipf.writestr("flag.txt", flag)

    with open(input_image, "rb") as f:
        image_data = f.read()
    with open(temp_zip, "rb") as f:
        zip_data = f.read()

    output_name = f"challenge_zip_{int(time.time())}.png"
    with open(output_name, "wb") as f:
        f.write(image_data + zip_data)

    os.remove(temp_zip)

    print(f"[+] Challenge Created: {output_name}")
    print(f"[+] Extract using: binwalk -e {output_name} && cat _{output_name}.extracted/flag.txt")


def insert_zsteg(input_image, flag):
    """Embed flag inside PNG metadata readable via zsteg."""
    img = Image.open(input_image)
    img_format = img.format.upper()

    if img_format != "PNG":
        raise ValueError("ZSteg method only works on PNG images.")

    meta = PngImagePlugin.PngInfo()
    meta.add_text("Flag", flag)

    output_name = f"challenge_zsteg_{int(time.time())}.png"
    img.save(output_name, pnginfo=meta)

    print(f"[+] Challenge Created: {output_name}")
    print(f"[+] Extract using: zsteg {output_name}")


# Command-line argument interface
def main():
    parser = argparse.ArgumentParser(description="ForensiX CLI - CTF Image Challenge Generator")

    parser.add_argument("--input", required=True, help="Input image (PNG/JPG)")
    parser.add_argument("--flag", required=True, help="Flag to hide (e.g. flag{secret})")
    parser.add_argument("--method", required=True, choices=["metadata", "strings", "zip", "zsteg"],
                        help="Stego method")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print("[!] Input file not found.")
        return

    if args.method == "metadata":
        insert_metadata(args.input, args.flag)
    elif args.method == "strings":
        insert_strings(args.input, args.flag)
    elif args.method == "zip":
        insert_zip(args.input, args.flag)
    elif args.method == "zsteg":
        insert_zsteg(args.input, args.flag)


if __name__ == "__main__":
    main()

