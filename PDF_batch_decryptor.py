"""
Super quick and dirty script to run qpdf --decrypt on problematic pdfs
"""
import json
import shutil
import fire
from tqdm import tqdm
from pathlib import Path, PosixPath
import subprocess
import time
from send2trash import send2trash


Path("./encrypted_pdf_to_trash/").mkdir(exist_ok=True)

def p(m: str) -> None:
    """
    Print a message to the console and append it to a log file.

    Args:
        m (str): The message to be printed and logged.
    """
    tqdm.write(m)
    with open("logs.txt", "a") as f:
        f.write(str(int(time.time())) + ":  " + m)
        f.write("\n")

def is_encrypted(pdf_file: str) -> bool:
    """
    Check if a PDF file is encrypted.

    Args:
        pdf_file (str): The path to the PDF file.

    Returns:
        tuple: A boolean indicating if the file is encrypted and the output of pdfinfo.
    """
    result = subprocess.run(
        ['pdfinfo', str(pdf_file)],
        capture_output=True,
        text=True,
        check=True
    )
    val = result.stdout
    encr_line = [l for l in val.splitlines() if l.startswith("Encrypted:")]
    assert len(encr_line) == 1, f"Number of lines: {len(encr_line)}"
    if " no" in encr_line[0]:
        return False, val
    else:
        return True, val

def ask() -> bool:
    """
    Ask the user if they want to decrypt a file.

    Returns:
        bool: True if the user wants to decrypt, False otherwise.
    """
    ans = input("Do you want to decrypt it? (y/n)\n>")
    if ans == "y":
        p(f"User said yes: '{ans}'")
        return True
    else:
        p(f"User said no: '{ans}'")
        return False

def decrypt(pdf_file: PosixPath) -> str:
    """
    Decrypt a PDF file using qpdf.

    Args:
        pdf_file (PosixPath): The path to the encrypted PDF file.

    Returns:
        str: The output of the decryption process.

    Raises:
        AssertionError: If the file is not encrypted or if the decryption fails.
    """
    assert is_encrypted(pdf_file)[0]

    decr_path = str(pdf_file) + "_decrypted"

    assert not Path(decr_path).exists()
    trash_list = [f.name for f in Path("./encrypted_pdf_to_trash/").iterdir()]
    assert pdf_file.name in trash_list

    try:
        result = subprocess.run(
            ['qpdf', "--decrypt", str(pdf_file), decr_path],
            capture_output=True,
            check=True
        )
        out = result.stdout.decode('utf-8', errors='replace')
    except subprocess.CalledProcessError as err:
        if err.returncode == 3:
            out = err.stderr.decode('utf-8', errors='replace')
        else:
            raise

    p(f"Output after decrypting:\n{out}")

    assert Path(decr_path).exists()
    assert not is_encrypted(decr_path)[0]
    send2trash(pdf_file)
    assert not pdf_file.exists()
    Path(decr_path).rename(pdf_file)
    assert pdf_file.exists()
    assert not is_encrypted(pdf_file)[0]
    return out


def duplicate_file(pdf_file: PosixPath) -> None:
    """
    Duplicate a PDF file to a trash directory.

    Args:
        pdf_file (PosixPath): The path to the PDF file to be duplicated.

    Raises:
        AssertionError: If the file already exists in the trash directory and the user doesn't confirm.
    """
    p(f"Duplicating {pdf_file}")
    trash_list = [f.name for f in Path("./encrypted_pdf_to_trash/").iterdir()]
    if pdf_file.name in trash_list:
        ans = input(f"Already present, is that okay? (y/n)\nFile: {pdf_file}\n>")
        if ans == "y":
            p(f"Not duplicating because user says it's okay: {ans}")
            return

    assert pdf_file.name not in trash_list
    shutil.copy2(str(pdf_file.absolute()), "./encrypted_pdf_to_trash/" + pdf_file.name)
    trash_list2 = [f.name for f in Path("./encrypted_pdf_to_trash/").iterdir()]
    assert len(trash_list2) != 0
    assert pdf_file.name in trash_list2
    p(f"Done duplicating {pdf_file}")

def get_pdf_info(path: str) -> dict:
    """
    Process PDF files in a given directory, checking for encryption and optionally decrypting them.

    Args:
        path (str): The directory path containing PDF files to process.

    Returns:
        dict: A dictionary containing information about each processed PDF file.
    """
    p(f"\nStarting script")
    pdf_info = {}
    encr_status = {}
    actions = {}
    file_list = [f for f in Path(path).rglob('*.pdf')]
    for pdf_file in tqdm(file_list):
        try:
            is_encr, val = is_encrypted(pdf_file=pdf_file)
        except Exception:
            continue
        key = str(pdf_file)
        pdf_info[key] = {"encryption": encr_status, "info": val}
        if is_encr:
            p(f"Is encrypted: {key}:\n{val}\n\n")

            pdf_info["decryption_output"] = None
            if ask():
                pdf_info[key]["action"] = True
                duplicate_file(pdf_file=pdf_file)
                try:
                    out = decrypt(pdf_file=pdf_file)
                except Exception as err:
                    p(f"Error when decrypting {pdf_file}\nError: {err}")
                    pdf_info["decryption_output"] = err
                    continue
                pdf_info["decryption_output"] = out
            else:
                pdf_info[key]["action"] = False

    with open(f"pdf_info.{int(time.time())}.json", "w") as f:
        f.write(json.dumps(pdf_info, indent=2))
    return pdf_info

if __name__ == '__main__':
    fire.Fire(get_pdf_info)
