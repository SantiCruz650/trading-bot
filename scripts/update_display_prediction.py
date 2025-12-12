#!/usr/bin/env python3

def update_display_prediction():
    """Update the displayPrediction function to be more modern"""
    
    # Get project root
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    with open(os.path.join(project_root, "frontend/index.html"), "r") as file:
        content = file.read()
    
    # Find the displayPrediction function
    start_marker = "function displayPrediction(data) {"
    end_marker = "predictionResult.classList.remove('d-none');"
    
    start_index = content.find(start_marker)
    if start_index == -1:
        print("Could not find displayPrediction function")
        return
    
    # Find the end of the function
    brace_count = 0
    end_index = start_index
    for i in range(start_index, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_index = i + 1
                break
    
    # Create a new modern displayPrediction function
    new_function = '''function displayPrediction(data) {
    const resultDiv = document.getElementById('prediction-details');
    
    // Check if data is valid
    if (!data || !data.ticker) {
        resultDiv.innerHTML = '<div class="alert alert-danger">Invalid prediction data received</div>';
        predictionResult.classList.remove('d-none');
        return;
    }
    
    let signalClass = '';
    let signalIcon = '';
    let signalBg = '';
    
    if (data.signal === 'BUY') {
        signalClass = 'signal-buy';
        signalIcon = '<i class="fas fa-arrow-up"></i>';
        signalBg = 'rgba(40, 167, 69, 0.1)';
    } else if (data.signal === 'SELL') {
        signalClass = 'signal-sell';
        signalIcon = '<i class="fas fa-arrow-down"></i>';
        signalBg = 'rgba(220, 53, 69, 0.1)';
    } else {
        signalClass = 'signal-hold';
        signalIcon = '<i class="fas fa-minus"></i>';
        signalBg = 'rgba(255, 193, 7, 0.1)';
    }

    resultDiv.innerHTML = `
        <div class="signal-display" style="background-color: ${signalBg};">
            <div class="signal-icon ${signalClass}">
                <i class="fab fa-${data.ticker === 'BTC' ? 'bitcoin' : 'ethereum'}"></i>
            </div>
            <div class="signal-details">
                <h3>${data.ticker} <span class="signal-badge ${signalClass}">${signalIcon} ${data.signal}</span></h3>
                <p class="mb-0">Signal generated at ${new Date(data.created_at).toLocaleString()}</p>
            </div>
        </div>
        
        <div class="price-display">
            <div class="price-item">
                <p class="mb-1 text-muted">Last Close</p>
                <p class="price-value">$${data.last_close}</p>
            </div>
            <div class="price-item">
                <p class="mb-1 text-muted">Predicted Close</p>
                <p class="price-value">$${data.predicted_close}</p>
            </div>
            <div class="price-item">
                <p class="mb-1 text-muted">Change</p>
                <p class="price-value ${data.predicted_close > data.last_close ? 'text-success' : 'text-danger'}">
                    ${data.predicted_close > data.last_close ? '+' : ''}${(data.predicted_close - data.last_close).toFixed(2)}
                </p>
            </div>
        </div>
        
        <div class="prediction-timestamp">
            <i class="fas fa-clock me-1"></i>
            Prediction created on ${new Date(data.created_at).toLocaleDateString()} at ${new Date(data.created_at).toLocaleTimeString()}
        </div>
    `;
    
    predictionResult.classList.remove('d-none');
}'''
    
    # Replace the function
    new_content = content[:start_index] + new_function + content[end_index:]
    
    with open(os.path.join(project_root, "frontend/index.html"), "w") as file:
        file.write(new_content)
    
    print("Updated displayPrediction function with modern design")

if __name__ == "__main__":
    update_display_prediction()
