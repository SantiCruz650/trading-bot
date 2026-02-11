#!/usr/bin/env python3

def add_modern_css():
    """Add modern CSS styles to make the prediction section more visually appealing"""
    
    with open("frontend/index.html", "r") as file:
        content = file.read()
    
    # Find the style section
    style_start = content.find("<style>")
    style_end = content.find("</style>") + 8
    
    if style_start == -1 or style_end == -1:
        print("Could not find style section")
        return
    
    # Extract the current styles
    current_styles = content[style_start:style_end]
    
    # Add new modern styles
    new_styles = current_styles + '''
        
        .bg-gradient {
            background: linear-gradient(135deg, var(--primary-color) 0%, #3a8eef 100%) !important;
        }
        
        .prediction-card {
            transition: all 0.3s ease;
            border: 1px solid rgba(74, 158, 255, 0.2);
        }
        
        .prediction-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            border-color: rgba(74, 158, 255, 0.4);
        }
        
        .signal-display {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            background: rgba(255, 255, 255, 0.05);
        }
        
        .signal-icon {
            font-size: 3rem;
            margin-right: 1rem;
        }
        
        .signal-details {
            flex: 1;
        }
        
        .price-display {
            display: flex;
            justify-content: space-between;
            margin: 1rem 0;
        }
        
        .price-item {
            text-align: center;
        }
        
        .price-value {
            font-size: 1.5rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        
        .prediction-timestamp {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.9rem;
        }
        
        .history-item {
            transition: all 0.2s ease;
            border-left: 4px solid var(--primary-color);
            padding-left: 1rem;
            margin-bottom: 1rem;
        }
        
        .history-item:hover {
            background: rgba(255, 255, 255, 0.05);
            transform: translateX(5px);
        }
        
        .loading-spinner {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 200px;
        }
        
        .spinner-border {
            width: 3rem;
            height: 3rem;
        }
        
        .input-group-text {
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .btn-lg {
            padding: 0.75rem 1.5rem;
            font-size: 1.1rem;
        }
'''
    
    # Replace the style section
    new_content = content[:style_start] + new_styles + content[style_end:]
    
    with open("frontend/index.html", "w") as file:
        file.write(new_content)
    
    print("Added modern CSS styles")

if __name__ == "__main__":
    add_modern_css()
