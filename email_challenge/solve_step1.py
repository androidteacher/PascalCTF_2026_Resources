import requests
import re
import sys
import time
import socket
import smtplib
from email.message import EmailMessage

# Configuration
SERVICE_URL = "https://surgoservice.ctf.pascalctf.it"
NC_HOST = "surgobot.ctf.pascalctf.it"
NC_PORT = 6005
SMTP_SERVER = "mail.skillissue.it" # From src.py analysis
# But wait, src.py uses internal networking. 
# We are external. We need to Reply to the email.
# The `surgo.ctf.pascalctf.it` is the "Email box" (Webmail likely).

# Let's inspect the `surgoservice` first to get an email.
def get_temp_email():
    s = requests.Session()
    # Assuming the site gives us an email on the homepage or via an API
    try:
        r = s.get(SERVICE_URL)
        # Look for an email pattern in the response
        # "Your email is: <span ...>user-xyz@...</span>"
        match = re.search(r'[\w\.-]+@[\w\.-]+\.skillissue\.it', r.text)
        if match:
            email = match.group(0)
            print(f"[*] Acquired email: {email}")
            return s, email
        else:
            # Maybe it needs a POST to generate?
            # Let's try to check the page content debug
            print("[-] Could not find email in main page.")
            print(r.text[:500])
            sys.exit(1)
    except Exception as e:
        print(f"[-] Error connecting to service: {e}")
        sys.exit(1)

# Usage logic:
# 1. Get email.
# 2. Connect to NC, provide email.
# 3. Wait for NC to say "We have sent you an email"
# 4. Check Webmail (surgo.ctf.pascalctf.it) or API ??
#    Wait, `surgo.ctf.pascalctf.it` is "Email box". It's likely a Roundcube or custom webmail where we login.
#    Since we have `surgoservice` for "account generator", likely `surgoservice` gives credentials.
#    Actually, typical CTF:
#    `surgoservice` gives you a tempoary inbox view content.

# Let's create a script that primarily explores the account generator first, 
# because without an account we can't do anything.

print("[*] Checking Email Generator...")
s, email_addr = get_temp_email()
