"""
Utility function to convert numbers to words (Indian numbering system)
Used for maintenance bill amount in words
"""


def number_to_words(num):
    """
    Convert a number to words in Indian numbering system
    Example: 1234.56 -> "One Thousand Two Hundred Thirty Four Rupees and Fifty Six Paise Only"
    """
    if num == 0:
        return "Zero Rupees Only"
    
    # Split into integer and decimal parts
    integer_part = int(num)
    decimal_part = round((num - integer_part) * 100)
    
    # Convert integer part
    rupees = convert_to_words(integer_part)
    rupees_text = f"{rupees} Rupees" if rupees else ""
    
    # Convert decimal part (paise)
    paise_text = ""
    if decimal_part > 0:
        paise = convert_to_words(decimal_part)
        paise_text = f" and {paise} Paise" if paise else ""
    
    result = f"{rupees_text}{paise_text} Only" if rupees_text or paise_text else "Zero Rupees Only"
    return result


def convert_to_words(n):
    """Convert integer to words"""
    if n == 0:
        return ""
    
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", 
             "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    if n < 10:
        return ones[n]
    elif n < 20:
        return teens[n - 10]
    elif n < 100:
        return tens[n // 10] + (" " + ones[n % 10] if n % 10 > 0 else "")
    elif n < 1000:
        hundred = ones[n // 100] + " Hundred"
        remainder = n % 100
        if remainder > 0:
            return hundred + " " + convert_to_words(remainder)
        return hundred
    elif n < 100000:  # Lakhs
        lakh = convert_to_words(n // 100000)
        remainder = n % 100000
        if remainder > 0:
            return convert_to_words(n // 100000) + " Lakh " + convert_to_words(remainder)
        return convert_to_words(n // 100000) + " Lakh"
    elif n < 10000000:  # Crores
        crore = convert_to_words(n // 10000000)
        remainder = n % 10000000
        if remainder > 0:
            return convert_to_words(n // 10000000) + " Crore " + convert_to_words(remainder)
        return convert_to_words(n // 10000000) + " Crore"
    else:
        # For very large numbers, handle recursively
        return convert_to_words(n // 10000000) + " Crore " + convert_to_words(n % 10000000)

