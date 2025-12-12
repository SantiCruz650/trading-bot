#!/usr/bin/env python3

def update_index_html():
    """Update the main index.html with MCrypto branding"""
    
    with open("frontend/index.html", "r") as file:
        content = file.read()
    
    # Replace the title
    content = content.replace("<title>HONDEX</title>", "<title>MCrypto - Trading Dashboard</title>")
    
    # Replace any HONDEX references in the content
    content = content.replace("HONDEX", "MCrypto")
    content = content.replace("Hondex", "MCrypto")
    content = content.replace("hondex", "mcrypto")
    
    # Update the password gate text
    content = content.replace("Welcome to HONDEX", "Welcome to MCrypto")
    content = content.replace("Enter password to access HONDEX", "Enter password to access MCrypto")
    
    # Update the password
    content = content.replace("HONDEX2024", "MCrypto2024")
    
    with open("frontend/index.html", "w") as file:
        file.write(content)
    
    print("Updated frontend/index.html with MCrypto branding")

if __name__ == "__main__":
    update_index_html()
