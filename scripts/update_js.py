#!/usr/bin/env python3

def update_js():
    """Update the JavaScript file with MCrypto branding and correct password"""
    
    with open("frontend/script.js", "r") as file:
        content = file.read()
    
    # Replace hondex references with mcrypto
    content = content.replace("hondex-form", "mcrypto-form")
    content = content.replace("hondexPassword", "mcrypto-password")
    content = content.replace("hondexError", "mcrypto-error")
    
    # Update the password check
    content = content.replace("HONDEX2024", "MCrypto2024")
    
    with open("frontend/script.js", "w") as file:
        file.write(content)
    
    print("Updated frontend/script.js with MCrypto branding and correct password")

if __name__ == "__main__":
    update_js()
