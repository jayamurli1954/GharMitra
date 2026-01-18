import re
import os

def salvage_raw_data(corrupted_path, output_file):
    print(f"\n--- Raw Data Salvage Started ---")
    print(f"Source: {corrupted_path}")
    
    if not os.path.exists(corrupted_path):
        print(f"❌ Source file not found: {corrupted_path}")
        return

    # Patterns to look for
    EMAIL_PATH = re.compile(rb'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    # Account codes are typically 4 digits near a name
    ACCOUNT_PATTERN = re.compile(rb'\b[1-9][0-9]{3}\b')
    # Potential names (Capitalized words followed by space and capitalized word)
    # This is broad and will catch many false positives, but we can filter
    NAME_PATTERN = re.compile(rb'[A-Z][a-z]+ [A-Z][a-z]+')
    
    salvaged_emails = set()
    salvaged_names = set()
    salvaged_accounts = set()

    try:
        with open(corrupted_path, 'rb') as f:
            content = f.read()
            
            print("Scanning for emails...")
            for match in EMAIL_PATH.finditer(content):
                salvaged_emails.add(match.group().decode('ascii', errors='ignore'))
                
            print("Scanning for potential account codes...")
            for match in ACCOUNT_PATTERN.finditer(content):
                salvaged_accounts.add(match.group().decode('ascii', errors='ignore'))

            print("Scanning for potential names...")
            for match in NAME_PATTERN.finditer(content):
                name = match.group().decode('ascii', errors='ignore')
                if len(name) > 5 and len(name) < 30:
                    salvaged_names.add(name)

        with open(output_file, 'w', encoding='utf-8') as out:
            out.write(f"RAW SALVAGE REPORT - {corrupted_path}\n")
            out.write("=" * 40 + "\n\n")
            
            out.write(f"EMAILS FOUND ({len(salvaged_emails)}):\n")
            for email in sorted(salvaged_emails):
                out.write(f" - {email}\n")
            
            out.write(f"\nACCOUNT CODES / 4-DIGIT VOUCHERS FOUND ({len(salvaged_accounts)}):\n")
            # Filter for common accounting ranges if possible
            for acc in sorted(salvaged_accounts):
                out.write(f" {acc}")
            out.write("\n")
            
            out.write(f"\nPOTENTIAL NAMES FOUND ({len(salvaged_names)}):\n")
            # Sort by length to put longer/more likely names first
            for name in sorted(list(salvaged_names), key=len, reverse=True):
                out.write(f" - {name}\n")

        print(f"\n✅ Salvage report written to: {os.path.abspath(output_file)}")
        print(f"Found {len(salvaged_emails)} emails and {len(salvaged_names)} potential names.")
        
    except Exception as e:
        print(f"❌ Salvage failed: {e}")

if __name__ == "__main__":
    CORRUPTED = "gharmitra_corrupted.db"
    REPORT = "salvage_report.txt"
    salvage_raw_data(CORRUPTED, REPORT)
