#!/usr/bin/env python3
import os
import re

def update_file_content(file_path, old_text, new_text):
    """Update content in a file"""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Replace old text with new text
        updated_content = content.replace(old_text, new_text)
        
        with open(file_path, 'w') as file:
            file.write(updated_content)
        
        print(f"Updated {file_path}")
        return True
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def rebrand_project():
    """Rebrand the project to MCrypto"""
    
    print("\n" + "="*60)
    print("         REBRANDING TO MCRYPTO")
    print("="*60)
    
    # Define the base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)
    
    # Files to update
    files_to_update = [
        "frontend/index.html",
        "backend/app/main.py",
        "ml_service/app/main.py"
    ]
    
    # Text replacements
    replacements = [
        ("HONDEX", "MCrypto"),
        ("Hondex", "MCrypto"),
        ("hondex", "mcrypto"),
        ("Trading Bot", "MCrypto"),
        ("trading bot", "MCrypto"),
        ("Trading-Bot", "MCrypto"),
        ("trading-bot", "mcrypto")
    ]
    
    # Update each file
    for file_path in files_to_update:
        if os.path.exists(file_path):
            print(f"\nUpdating {file_path}:")
            for old_text, new_text in replacements:
                update_file_content(file_path, old_text, new_text)
        else:
            print(f"File not found: {file_path}")
    
    # Update the README if it exists
    readme_path = os.path.join(base_dir, "README.md")
    if os.path.exists(readme_path):
        print(f"\nUpdating README.md:")
        for old_text, new_text in replacements:
            update_file_content(readme_path, old_text, new_text)
    
    # Update the project name in the frontend title
    frontend_index = os.path.join(base_dir, "frontend/index.html")
    if os.path.exists(frontend_index):
        print(f"\nUpdating frontend title:")
        update_file_content(frontend_index, "<title>HONDEX</title>", "<title>MCrypto</title>")
        update_file_content(frontend_index, "<title>Trading Bot</title>", "<title>MCrypto</title>")
    
    # Update the password gate text
    if os.path.exists(frontend_index):
        print(f"\nUpdating password gate text:")
        update_file_content(frontend_index, "HONDEX2024", "MCrypto2024")
    
    print("\n" + "="*60)
    print("         REBRANDING COMPLETE")
    print("="*60)
    print("\nYour project has been rebranded to MCrypto!")
    print("Don't forget to:")
    print("1. Restart your services to see the changes")
    print("2. Update any documentation with the new name")
    print("3. Update the password from HONDEX2024 to MCrypto2024")
    print("="*60)

if __name__ == "__main__":
    rebrand_project()
