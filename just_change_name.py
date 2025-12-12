#!/usr/bin/env python3

def just_change_name():
    """Only change the name from HONDEX to MCrypto without changing anything else"""
    
    with open("frontend/index.html", "r") as file:
        content = file.read()
    
    # Only change the name references
    content = content.replace("HONDEX", "MCrypto")
    content = content.replace("Hondex", "MCrypto")
    content = content.replace("hondex", "mcrypto")
    
    # Change the password
    content = content.replace("HONDEX2024", "MCrypto2024")
    
    with open("frontend/index.html", "w") as file:
        file.write(content)
    
    print("Changed name from HONDEX to MCrypto")

if __name__ == "__main__":
    just_change_name()
