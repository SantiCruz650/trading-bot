#!/usr/bin/env python3

def update_js_error_handling():
    """Update the JavaScript with better error handling"""
    
    with open("index.html", "r") as file:
        content = file.read()
    
    # Update the handlePrediction function
    start_marker = "function handlePrediction(e) {"
    end_marker = "    })"
    
    start_index = content.find(start_marker)
    if start_index == -1:
        print("Could not find handlePrediction function")
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
    
    # Create a new handlePrediction function with better error handling
    new_function = '''function handlePrediction(e) {
    e.preventDefault();
    const ticker = document.getElementById('prediction-ticker').value;

    // Disable the form button and show loading state
    const submitBtn = predictionForm.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';

    fetch(`${API_URL}/predict/${ticker}`, {
        method: 'POST',
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
        console.log('Prediction data:', data); // Debug log
        
        // Display the prediction in a modal
        displayPredictionModal(data);
        
        // Add to history
        loadPredictionHistory();
    })
    .catch(error => {
        console.error('Prediction error:', error);
        
        // Show a more detailed error message
        let errorMessage = 'Failed to get prediction. Please try again.';
        
        if (error.message) {
            errorMessage += ` Error: ${error.message}`;
        }
        
        alert(errorMessage);
    })
    .finally(() => {
        // Restore the button
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
    });
}'''
    
    # Replace the function in the HTML
    new_content = content[:start_index] + new_function + content[end_index:]
    
    with open("index.html", "w") as file:
        file.write(new_content)
    
    print("Updated handlePrediction function with better error handling")

if __name__ == "__main__":
    update_js_error_handling()
