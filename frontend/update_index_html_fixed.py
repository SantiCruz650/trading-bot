#!/usr/bin/env python3

def update_index_html():
    """Update the index.html file to use the fixed JavaScript file"""
    
    with open("frontend/index.html", "r") as file:
        content = file.read()
    
    # Replace the old script with the fixed one
    content = content.replace('mcrypto_script.js', 'fixed_script.js')
    
    with open("frontend/index.html", "w") as file:
        file.write(content)
    
    print("Updated frontend/index.html to use fixed_script.js")

if __name__ == "__main__":
    update_index_html()
