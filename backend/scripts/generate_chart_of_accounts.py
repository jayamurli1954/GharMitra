"""
Generate Chart of Accounts from Chart_of_Accounts.txt with proper account codes
Following standard accounting practice with gaps for future accounts
"""

import json
import re
from pathlib import Path

# Account code ranges
ASSET_START = 1000
LIABILITY_START = 2000
CAPITAL_START = 3000
INCOME_START = 4000
EXPENSE_START = 5000

def parse_accounts():
    """Parse Chart_of_Accounts.txt and generate structured accounts with codes"""
    
    file_path = Path(__file__).parent.parent.parent / 'Chart_of_Accounts.txt'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    accounts = []
    lines = content.split('\n')
    
    current_type = None
    current_category = None
    code_counter = {
        'asset': ASSET_START,
        'liability': LIABILITY_START,
        'capital': CAPITAL_START,
        'income': INCOME_START,
        'expense': EXPENSE_START
    }
    
    category_base = {}  # Track base code for each category
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect main sections
        if '### 1. ASSETS' in line:
            current_type = 'asset'
            code_counter['asset'] = ASSET_START
        elif '### 2. LIABILITIES' in line:
            current_type = 'liability'
            code_counter['liability'] = LIABILITY_START
        elif '### 3. INCOME' in line:
            current_type = 'income'
            code_counter['income'] = INCOME_START
        elif '### 4. EXPENSES' in line:
            current_type = 'expense'
            code_counter['expense'] = EXPENSE_START
        
        # Detect categories (bold text with **)
        if line.startswith('**') and line.endswith('**') and not line.startswith('###'):
            category = line.replace('**', '').strip()
            current_category = category
            
            # Assign base code for this category (increment by 100 for major categories)
            if current_type:
                category_key = f"{current_type}_{category}"
                if category_key not in category_base:
                    # Use next available hundred
                    base = code_counter[current_type]
                    # Round up to next hundred if not already
                    category_base[category_key] = ((base // 100) * 100) + 100 if base % 100 != 0 else base
                    code_counter[current_type] = category_base[category_key]
        
        # Parse account entries: - **Account Name**: Description
        if line.startswith('- **') and ':' in line:
            match = re.match(r'- \*\*(.+?)\*\*: (.+)', line)
            if match and current_type:
                account_name = match.group(1).strip()
                description = match.group(2).strip()
                
                # Get base code for current category
                if current_category:
                    category_key = f"{current_type}_{current_category}"
                    if category_key in category_base:
                        base = category_base[category_key]
                    else:
                        base = code_counter[current_type]
                        category_base[category_key] = base
                else:
                    base = code_counter[current_type]
                
                # Assign code (increment by 10 within category)
                # Count how many accounts already in this category
                accounts_in_category = len([a for a in accounts 
                                          if a.get('category') == current_category and a.get('type') == current_type])
                account_code = base + (accounts_in_category * 10)
                
                accounts.append({
                    'code': str(account_code),
                    'name': account_name,
                    'type': current_type,
                    'description': description,
                    'category': current_category or ''
                })
                
                # Update counter
                code_counter[current_type] = max(code_counter[current_type], account_code + 10)
        
        # Handle Capital/Equity (part of Liabilities section)
        if current_type == 'liability' and ('Funds (Capital/Corpus)' in line or 'CAPITAL' in line.upper() or 'EQUITY' in line.upper()):
            current_type = 'capital'
            if 'capital' not in code_counter:
                code_counter['capital'] = CAPITAL_START
        
        i += 1
    
    return accounts

def main():
    accounts = parse_accounts()
    
    # Print summary
    print(f"Total accounts: {len(accounts)}")
    print("\nBy type:")
    for acc_type in ['asset', 'liability', 'capital', 'income', 'expense']:
        count = len([a for a in accounts if a['type'] == acc_type])
        if count > 0:
            print(f"  {acc_type.capitalize()}: {count}")
    
    # Save to JSON
    output_path = Path(__file__).parent.parent / 'chart_of_accounts.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to {output_path}")
    print("\nSample accounts (first 10):")
    for acc in accounts[:10]:
        print(f"  {acc['code']} - {acc['name']}")

if __name__ == '__main__':
    main()

