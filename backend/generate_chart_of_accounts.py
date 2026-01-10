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

def parse_chart_of_accounts():
    """Parse the Chart_of_Accounts.txt file and generate account codes"""
    
    with open('../Chart_of_Accounts.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    accounts = []
    current_type = None
    current_category = None
    code_counter = {
        'asset': 1000,
        'liability': 2000,
        'capital': 3000,
        'income': 4000,
        'expense': 5000
    }
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Detect main category (ASSETS, LIABILITIES, etc.)
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
        
        # Detect subcategories
        if line.startswith('**Current Assets**'):
            code_counter['asset'] = 1000
        elif line.startswith('**Fixed Assets**'):
            code_counter['asset'] = 1500
        elif line.startswith('**Investments**'):
            code_counter['asset'] = 1800
        elif line.startswith('**Other Assets**'):
            code_counter['asset'] = 1900
        elif line.startswith('**Current Liabilities**'):
            code_counter['liability'] = 2000
        elif line.startswith('**Long-term Liabilities**'):
            code_counter['liability'] = 2500
        elif line.startswith('**Funds (Capital/Corpus)**'):
            code_counter['capital'] = 3000
        elif line.startswith('**Statutory Funds**'):
            code_counter['capital'] = 3000
        elif line.startswith('**Other Funds**'):
            code_counter['capital'] = 3100
        elif line.startswith('**General Fund**'):
            code_counter['capital'] = 3200
        elif line.startswith('**Maintenance Income (Primary Income)**'):
            code_counter['income'] = 4000
        elif line.startswith('**Fund Contributions**'):
            code_counter['income'] = 4100
        elif line.startswith('**Service Charges**'):
            code_counter['income'] = 4200
        elif line.startswith('**Other Income**'):
            code_counter['income'] = 4300
        elif line.startswith('**Administrative Expenses**'):
            code_counter['expense'] = 5000
        elif line.startswith('**Building Maintenance Expenses**'):
            code_counter['expense'] = 5200
        elif line.startswith('**Utilities**'):
            code_counter['expense'] = 5400
        elif line.startswith('**Security and Safety**'):
            code_counter['expense'] = 5500
        elif line.startswith('**Amenity Expenses**'):
            code_counter['expense'] = 5600
        elif line.startswith('**Statutory Expenses**'):
            code_counter['expense'] = 5700
        elif line.startswith('**Financial Expenses**'):
            code_counter['expense'] = 5800
        elif line.startswith('**Depreciation**'):
            code_counter['expense'] = 5900
        elif line.startswith('**Taxes and Legal**'):
            code_counter['expense'] = 5910
        elif line.startswith('**Other Expenses**'):
            code_counter['expense'] = 5990
        
        # Parse account entries (format: - **Account Name**: Description)
        if line.startswith('- **') and ':' in line:
            match = re.match(r'- \*\*(.+?)\*\*: (.+)', line)
            if match:
                name = match.group(1).strip()
                description = match.group(2).strip()
                
                if current_type:
                    # Generate code with gaps (increment by 10)
                    code = str(code_counter[current_type])
                    code_counter[current_type] += 10
                    
                    accounts.append({
                        'code': code,
                        'name': name,
                        'type': current_type,
                        'description': description
                    })
    
    return accounts

if __name__ == '__main__':
    accounts = parse_chart_of_accounts()
    
    print(f"Generated {len(accounts)} accounts")
    print("\nSample accounts:")
    for acc in accounts[:10]:
        print(f"{acc['code']} - {acc['name']} ({acc['type']})")
    
    # Generate Python list format
    print("\n\n# Chart of Accounts for backend")
    print("CHART_OF_ACCOUNTS = [")
    for acc in accounts:
        print(f"    {{'code': '{acc['code']}', 'name': '{acc['name']}', 'type': '{acc['type']}', 'description': '{acc['description']}'}},")
    print("]")

