#!/usr/bin/env python3

def update_index_html():
    """Update the index.html file to use the new JavaScript file"""
    
    with open("frontend/index.html", "r") as file:
        content = file.read()
    
    # Replace the old script.js with mcrypto_script.js
    content = content.replace('script.js', 'mcrypto_script.js')
    
    with open("frontend/index.html", "w") as file:
        file.write(content)
    
    print("Updated frontend/index.html to use mcrypto_script.js")

if __name__ == "__main__":
    update_index_html()
