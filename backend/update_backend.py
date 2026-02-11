#!/usr/bin/env python3

def update_backend():
    """Update the backend with MCrypto branding"""
    
    with open("backend/app/main.py", "r") as file:
        content = file.read()
    
    # Replace any HONDEX references in the content
    content = content.replace("HONDEX", "MCrypto")
    content = content.replace("Hondex", "MCrypto")
    content = content.replace("hondex", "mcrypto")
    content = content.replace("Trading Bot Backend API", "MCrypto Trading API")
    
    with open("backend/app/main.py", "w") as file:
        file.write(content)
    
    print("Updated backend/app/main.py with MCrypto branding")

if __name__ == "__main__":
    update_backend()
