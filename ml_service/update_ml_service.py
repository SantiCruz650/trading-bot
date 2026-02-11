#!/usr/bin/env python3

def update_ml_service():
    """Update the ML service with MCrypto branding"""
    
    with open("ml_service/app/main.py", "r") as file:
        content = file.read()
    
    # Replace any HONDEX references in the content
    content = content.replace("HONDEX", "MCrypto")
    content = content.replace("Hondex", "MCrypto")
    content = content.replace("hondex", "mcrypto")
    
    with open("ml_service/app/main.py", "w") as file:
        file.write(content)
    
    print("Updated ml_service/app/main.py with MCrypto branding")

if __name__ == "__main__":
    update_ml_service()
