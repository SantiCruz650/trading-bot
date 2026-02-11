#!/usr/bin/env python3

def fix_password():
    """Fix the password in the frontend"""
    
    with open("frontend/index.html", "r") as file:
        content = file.read()
    
    # Check if the password is already correct
    if "MCrypto2024" in content:
        print("Password is already set to MCrypto2024")
        return
    
    # Replace the password
    content = content.replace("HONDEX2024", "MCrypto2024")
    
    with open("frontend/index.html", "w") as file:
        file.write(content)
    
    print("Password updated to MCrypto2024")

if __name__ == "__main__":
    fix_password()
