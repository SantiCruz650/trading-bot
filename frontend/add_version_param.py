#!/usr/bin/env python3

def add_version_param():
    """Add a version parameter to CSS and JS files to break caching"""
    
    with open("frontend/index.html", "r") as file:
        content = file.read()
    
    # Add version parameter to CSS and JS files
    content = re.sub(r'(<link[^>]+href="[^"]+\.css)", r'\1?v=2.0"', content)
    content = re.sub(r'(<script[^>]+src="[^"]+\.js)", r'\1?v=2.0"', content)
    
    with open("frontend/index.html", "w") as file:
        file.write(content)
    
    print("Added version parameters to break caching")

if __name__ == "__main__":
    add_version_param()
