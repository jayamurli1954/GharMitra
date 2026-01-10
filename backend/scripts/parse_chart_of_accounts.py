"""
Script to parse Chart_of_Accounts.txt and generate account codes with proper gaps
Following standard accounting practice:
- Assets: 1000-1999
- Liabilities: 2000-2999
- Capital/Equity: 3000-3999
- Income: 4000-4999
- Expenses: 5000-5999
"""

import re
from typing import List, Dict, Tuple

def parse_chart_of_accounts(file_path: str) -> List[Dict]:
    """Parse the chart of accounts file and return structured account data"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    accounts = []
    current_type = None
    current_subtype = None
    code_counter = {
        'asset': 1000,
        'liability': 2000,
        'capital': 3000,
        'income': 4000,
        'expense': 5000
    }
    
    # Track subcategories for better code organization
    subtype_counters = {}
    
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect main category
        if line.startswith('### 1. ASSETS'):
            current_type = 'asset'
            code_counter['asset'] = 1000
        elif line.startswith('### 2. LIABILITIES'):
            current_type = 'liability'
            code_counter['liability'] = 2000
        elif line.startswith('### 3. INCOME'):
            current_type = 'income'
            code_counter['income'] = 4000
        elif line.startswith('### 4. EXPENSES'):
            current_type = 'expense'
            code_counter['expense'] = 5000
        elif 'CAPITAL' in line.upper() or 'EQUITY' in line.upper() or 'FUNDS' in line.upper():
            if current_type == 'liability':
                # Capital/Equity is part of liabilities section
                current_type = 'capital'
                code_counter['capital'] = 3000
        
        # Detect subcategories (bold text)
        if line.startswith('**') and line.endswith('**'):
            subtype = line.replace('**', '').strip()
            current_subtype = subtype
            # Reset subtype counter when entering new subtype
            subtype_key = f"{current_type}_{subtype}"
            if subtype_key not in subtype_counters:
                subtype_counters[subtype_key] = 0
        
        # Parse account entries (lines starting with - **Account Name**: Description)
        if line.startswith('- **') and ':' in line:
            # Extract account name and description
            match = re.match(r'- \*\*(.+?)\*\*: (.+)', line)
            if match:
                account_name = match.group(1).strip()
                description = match.group(2).strip()
                
                if current_type:
                    # Determine code based on type and subtype
                    subtype_key = f"{current_type}_{current_subtype}" if current_subtype else current_type
                    
                    # Get base code for this type
                    base_code = code_counter[current_type]
                    
                    # For subcategories, use increments of 10 or 100
                    if current_subtype:
                        if subtype_key not in subtype_counters:
                            subtype_counters[subtype_key] = 0
                        
                        # Use increments of 10 for better organization
                        account_code = base_code + (subtype_counters[subtype_key] * 10)
                        subtype_counters[subtype_key] += 1
                    else:
                        account_code = code_counter[current_type]
                        code_counter[current_type] += 10  # Leave gaps of 10
                    
                    accounts.append({
                        'code': str(account_code),
                        'name': account_name,
                        'type': current_type,
                        'description': description,
                        'subtype': current_subtype
                    })
        
        i += 1
    
    return accounts


def generate_account_codes_with_gaps(accounts: List[Dict]) -> List[Dict]:
    """
    Reorganize accounts with proper code gaps following standard accounting practice
    """
    # Group by type and subtype
    organized = {
        'asset': {
            'Current Assets': [],
            'Fixed Assets': [],
            'Investments': [],
            'Other Assets': []
        },
        'liability': {
            'Current Liabilities': [],
            'Long-term Liabilities': [],
            'Funds (Capital/Corpus)': []
        },
        'capital': {
            'Statutory Funds': [],
            'Other Funds': [],
            'General Fund': []
        },
        'income': {
            'Maintenance Income (Primary Income)': [],
            'Fund Contributions': [],
            'Service Charges': [],
            'Other Income': []
        },
        'expense': {
            'Administrative Expenses': [],
            'Building Maintenance Expenses': [],
            'Utilities': [],
            'Security and Safety': [],
            'Amenity Expenses': [],
            'Statutory Expenses': [],
            'Financial Expenses': [],
            'Depreciation': [],
            'Taxes and Legal': [],
            'Other Expenses': []
        }
    }
    
    # Categorize accounts
    for account in accounts:
        acc_type = account['type']
        subtype = account.get('subtype', '')
        
        # Map to organized structure
        if acc_type == 'asset':
            if 'Current' in subtype or 'Cash' in subtype or 'Receivable' in subtype or 'Advance' in subtype or 'Inventory' in subtype:
                organized['asset']['Current Assets'].append(account)
            elif 'Fixed' in subtype or 'Building' in subtype or 'Amenity' in subtype or 'Office' in subtype or 'Depreciation' in subtype:
                organized['asset']['Fixed Assets'].append(account)
            elif 'Investment' in subtype:
                organized['asset']['Investments'].append(account)
            else:
                organized['asset']['Other Assets'].append(account)
        elif acc_type == 'liability':
            if 'Current' in subtype or 'Payable' in subtype or 'Statutory' in subtype or 'Member' in subtype or 'Provision' in subtype:
                organized['liability']['Current Liabilities'].append(account)
            elif 'Long-term' in subtype or 'Loan' in subtype:
                organized['liability']['Long-term Liabilities'].append(account)
            elif 'Fund' in subtype or 'Capital' in subtype or 'Corpus' in subtype:
                organized['liability']['Funds (Capital/Corpus)'].append(account)
            else:
                organized['liability']['Current Liabilities'].append(account)
        elif acc_type == 'capital':
            organized['capital']['Statutory Funds'].append(account)
        elif acc_type == 'income':
            if 'Maintenance' in subtype:
                organized['income']['Maintenance Income (Primary Income)'].append(account)
            elif 'Fund' in subtype:
                organized['income']['Fund Contributions'].append(account)
            elif 'Service' in subtype or 'Club' in subtype or 'Amenity' in subtype:
                organized['income']['Service Charges'].append(account)
            else:
                organized['income']['Other Income'].append(account)
        elif acc_type == 'expense':
            if 'Administrative' in subtype or 'Staff' in subtype or 'Office' in subtype or 'Professional' in subtype:
                organized['expense']['Administrative Expenses'].append(account)
            elif 'Building' in subtype or 'Lift' in subtype or 'Generator' in subtype or 'Electrical' in subtype or 'Plumbing' in subtype or 'Civil' in subtype or 'Cleaning' in subtype or 'Garden' in subtype:
                organized['expense']['Building Maintenance Expenses'].append(account)
            elif 'Electricity' in subtype or 'Water' in subtype or 'Utility' in subtype:
                organized['expense']['Utilities'].append(account)
            elif 'Security' in subtype or 'Safety' in subtype:
                organized['expense']['Security and Safety'].append(account)
            elif 'Amenity' in subtype or 'Clubhouse' in subtype or 'Recreation' in subtype:
                organized['expense']['Amenity Expenses'].append(account)
            elif 'Statutory' in subtype or 'Property Tax' in subtype:
                organized['expense']['Statutory Expenses'].append(account)
            elif 'Interest' in subtype or 'Bank' in subtype or 'Loan' in subtype or 'Financial' in subtype:
                organized['expense']['Financial Expenses'].append(account)
            elif 'Depreciation' in subtype:
                organized['expense']['Depreciation'].append(account)
            elif 'Tax' in subtype or 'Legal' in subtype:
                organized['expense']['Taxes and Legal'].append(account)
            else:
                organized['expense']['Other Expenses'].append(account)
    
    # Generate codes with proper gaps
    final_accounts = []
    code_ranges = {
        'asset': {'start': 1000, 'current': 1000},
        'liability': {'start': 2000, 'current': 2000},
        'capital': {'start': 3000, 'current': 3000},
        'income': {'start': 4000, 'current': 4000},
        'expense': {'start': 5000, 'current': 5000}
    }
    
    for acc_type, categories in organized.items():
        base_code = code_ranges[acc_type]['current']
        code_increment = 0
        
        for category_name, category_accounts in categories.items():
            if not category_accounts:
                continue
            
            # Start each category at a round number (e.g., 1000, 1100, 1200)
            category_base = base_code + (code_increment * 100)
            account_index = 0
            
            for account in category_accounts:
                # Use increments of 10 within each category
                account_code = category_base + (account_index * 10)
                account['code'] = str(account_code)
                final_accounts.append(account)
                account_index += 1
            
            # Move to next category (increment by 100 to leave room)
            code_increment += 1
        
        # Update current position for this type
        code_ranges[acc_type]['current'] = base_code + (code_increment * 100)
    
    return final_accounts


if __name__ == '__main__':
    # Parse the file
    file_path = '../Chart_of_Accounts.txt'
    accounts = parse_chart_of_accounts(file_path)
    
    # Reorganize with proper gaps
    final_accounts = generate_account_codes_with_gaps(accounts)
    
    # Print summary
    print(f"Total accounts parsed: {len(final_accounts)}")
    print("\nAccount distribution by type:")
    for acc_type in ['asset', 'liability', 'capital', 'income', 'expense']:
        count = len([a for a in final_accounts if a['type'] == acc_type])
        print(f"  {acc_type.capitalize()}: {count}")
    
    # Print first 20 accounts as sample
    print("\nSample accounts (first 20):")
    for account in final_accounts[:20]:
        print(f"  {account['code']} - {account['name']} ({account['type']})")
    
    # Export to JSON for backend use
    import json
    with open('../chart_of_accounts_parsed.json', 'w', encoding='utf-8') as f:
        json.dump(final_accounts, f, indent=2, ensure_ascii=False)
    
    print(f"\nExported {len(final_accounts)} accounts to chart_of_accounts_parsed.json")

