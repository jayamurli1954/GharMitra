"""Chart of Accounts search API"""
from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel
import os
import re

router = APIRouter()


class ChartAccountSuggestion(BaseModel):
    """Model for chart of accounts suggestion"""
    name: str
    description: str
    category: str  # e.g., "Current Assets", "Income", etc.
    sub_category: Optional[str] = None  # e.g., "Cash and Bank Accounts", "Receivables", etc.
    suggested_code: Optional[str] = None  # Suggested account code based on category


def parse_chart_of_accounts() -> List[dict]:
    """Parse Chart_of_Accounts.txt file and extract account information"""
    # Try multiple possible paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    chart_file = os.path.join(base_dir, 'Chart_of_Accounts.txt')
    
    # If not found, try relative to current file
    if not os.path.exists(chart_file):
        chart_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Chart_of_Accounts.txt')
    
    if not os.path.exists(chart_file):
        return []
    
    accounts = []
    current_category = None
    current_sub_category = None
    
    with open(chart_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Detect main category (ASSETS, LIABILITIES, INCOME, EXPENSES)
        if line.startswith('###'):
            if 'ASSETS' in line.upper():
                current_category = 'Assets'
            elif 'LIABILITIES' in line.upper():
                current_category = 'Liabilities'
            elif 'INCOME' in line.upper():
                current_category = 'Income'
            elif 'EXPENSES' in line.upper() or 'EXPENDITURE' in line.upper():
                current_category = 'Expenses'
            current_sub_category = None
            continue
        
        # Detect sub-category (e.g., **Current Assets**, *Cash and Bank Accounts*)
        if line.startswith('**'):
            # Main sub-category like "Current Assets"
            current_sub_category = line.replace('**', '').strip()
            continue
        elif line.startswith('*') and not line.startswith('**'):
            # Sub-sub-category like "*Cash and Bank Accounts*"
            current_sub_category = line.replace('*', '').strip()
            continue
        
        # Parse account entry: "- **Account Name**: Description"
        if line.startswith('- **'):
            match = re.match(r'- \*\*(.+?)\*\*: (.+)', line)
            if match:
                account_name = match.group(1).strip()
                description = match.group(2).strip()
                
                # Determine account type based on category
                account_type = None
                suggested_code = None
                if current_category == 'Assets':
                    account_type = 'asset'
                    if 'Current Assets' in str(current_sub_category):
                        suggested_code = '1'  # 1000-1999 range
                    elif 'Fixed Assets' in str(current_sub_category):
                        suggested_code = '1'  # 1000-1999 range
                elif current_category == 'Liabilities':
                    account_type = 'liability'
                    suggested_code = '2'  # 2000-2999 range
                elif current_category == 'Income':
                    account_type = 'income'
                    suggested_code = '4'  # 4000-4999 range
                elif current_category == 'Expenses':
                    account_type = 'expense'
                    suggested_code = '5'  # 5000-5999 range
                
                accounts.append({
                    'name': account_name,
                    'description': description,
                    'category': current_category or '',
                    'sub_category': current_sub_category or '',
                    'type': account_type,
                    'suggested_code': suggested_code
                })
    
    return accounts


@router.get("/search", response_model=List[ChartAccountSuggestion])
async def search_chart_of_accounts(
    query: str = Query(..., min_length=3, description="Search query (minimum 3 characters)"),
    account_type: Optional[str] = Query(None, description="Filter by account type: asset, liability, income, expense")
):
    """Search chart of accounts by name or description"""
    all_accounts = parse_chart_of_accounts()
    
    if not all_accounts:
        return []
    
    # Filter by account type if provided
    if account_type:
        all_accounts = [acc for acc in all_accounts if acc.get('type') == account_type]
    
    # Search in name and description (case-insensitive)
    query_lower = query.lower()
    matching_accounts = []
    
    for account in all_accounts:
        name_match = query_lower in account['name'].lower()
        desc_match = query_lower in account['description'].lower()
        
        if name_match or desc_match:
            # Prioritize name matches
            priority = 0 if name_match else 1
            matching_accounts.append((priority, account))
    
    # Sort by priority (name matches first), then alphabetically
    matching_accounts.sort(key=lambda x: (x[0], x[1]['name'].lower()))
    
    # Return top 20 matches
    results = [
        ChartAccountSuggestion(
            name=acc['name'],
            description=acc['description'],
            category=acc['category'],
            sub_category=acc['sub_category'] if acc['sub_category'] else None,
            suggested_code=acc['suggested_code']
        )
        for _, acc in matching_accounts[:20]
    ]
    
    return results

