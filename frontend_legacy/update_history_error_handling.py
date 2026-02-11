#!/usr/bin/env python3

def update_history_error_handling():
    """Update the loadPredictionHistory function with better error handling"""
    
    with open("index.html", "r") as file:
        content = file.read()
    
    # Update the loadPredictionHistory function
    start_marker = "function loadPredictionHistory() {"
    end_marker = "    })"
    
    start_index = content.find(start_marker)
    if start_index == -1:
        print("Could not find loadPredictionHistory function")
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
    
    # Create a new loadPredictionHistory function with better error handling
    new_function = '''function loadPredictionHistory() {
    fetch(`${API_URL}/my-predictions`, {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('History data:', data); // Debug log
        historyList.innerHTML = '';
        
        if (!data || data.length === 0) {
            historyList.innerHTML = '<p class="text-muted text-center">No predictions yet.</p>';
            return;
        }

        data.forEach(prediction => {
            let signalClass = '';
            let signalIcon = '';
            
            if (prediction.signal === 'BUY') {
                signalClass = 'signal-buy';
                signalIcon = '<i class="fas fa-arrow-up me-1"></i>';
            } else if (prediction.signal === 'SELL') {
                signalClass = 'signal-sell';
                signalIcon = '<i class="fas fa-arrow-down me-1"></i>';
            } else {
                signalClass = 'signal-hold';
                signalIcon = '<i class="fas fa-minus me-1"></i>';
            }

            const predictionItem = document.createElement('div');
            predictionItem.className = 'card mb-3 history-item';
            predictionItem.innerHTML = `
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <div class="d-flex align-items-center">
                                <i class="fab fa-${prediction.ticker === 'BTC' ? 'bitcoin' : 'ethereum'} fa-2x text-primary me-2"></i>
                                <div>
                                    <h6 class="mb-0">${prediction.ticker}</h6>
                                    <span class="signal-badge ${signalClass}">${signalIcon}${prediction.signal}</span>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="row">
                                <div class="col-6">
                                    <p class="mb-1 text-muted">Last Close</p>
                                    <p class="mb-0">$${prediction.last_close}</p>
                                </div>
                                <div class="col-6">
                                    <p class="mb-1 text-muted">Predicted Close</p>
                                    <p class="mb-0">$${prediction.predicted_close}</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 text-end">
                            <p class="mb-1 text-muted">Created</p>
                            <p class="mb-0">${new Date(prediction.created_at).toLocaleDateString()}</p>
                        </div>
                    </div>
                </div>
            `;
            historyList.appendChild(predictionItem);
        });
    })
    .catch(error => {
        console.error('History error:', error);
        
        // Show a more detailed error message
        let errorMessage = 'Failed to load prediction history.';
        
        if (error.message) {
            errorMessage += ` Error: ${error.message}`;
        }
        
        historyList.innerHTML = `<p class="text-danger text-center">${errorMessage}</p>`;
    });
}'''
    
    # Replace the function in the HTML
    new_content = content[:start_index] + new_function + content[end_index:]
    
    with open("index.html", "w") as file:
        file.write(new_content)
    
    print("Updated loadPredictionHistory function with better error handling")

if __name__ == "__main__":
    update_history_error_handling()
