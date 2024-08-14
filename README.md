# PDF Batch Decryptor
Super quick and dirty script to call "qpdf --decrypt" on all PDF files that `pdfinfo` deems encrypted.

## Usage

1. Ensure you have the required dependencies installed:
   - Python 3.x
   - qpdf
   - pdfinfo (usually part of the poppler-utils package)

2. Install the Python dependencies:
   ```
   pip install fire tqdm send2trash
   ```

3. Run the script with the path to the directory containing PDF files:
   ```
   python PDF_batch_decryptor.py /path/to/pdf/directory
   ```

4. The script will:
   - Check each PDF file for encryption
   - Ask if you want to decrypt each encrypted file
   - Decrypt the files you choose to decrypt
   - Move the original encrypted files to a trash directory
   - Generate a JSON file with information about the processed PDFs

Note: Make sure you have the necessary permissions to read and write files in the specified directory.
