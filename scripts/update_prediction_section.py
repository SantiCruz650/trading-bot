#!/usr/bin/env python3

def update_prediction_section():
    """Update the prediction section to be more modern and visually appealing"""
    
    with open("frontend/index.html", "r") as file:
        content = file.read()
    
    # Find and replace the prediction section
    start_marker = '<!-- Dashboard Section (Hidden by default) -->'
    end_marker = '<!-- Backtest Section (Hidden by default) -->'
    
    start_index = content.find(start_marker)
    end_index = content.find(end_marker)
    
    if start_index == -1 or end_index == -1:
        print("Could not find prediction section to update")
        return
    
    # Create a new modern prediction section
    new_prediction_section = '''<!-- Dashboard Section (Hidden by default) -->
        <div id="dashboard-section" class="d-none">
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card prediction-card">
                        <div class="card-header bg-gradient">
                            <h5 class="mb-0">
                                <i class="fas fa-chart-line me-2"></i>Get Prediction
                            </h5>
                        </div>
                        <div class="card-body">
                            <form id="prediction-form">
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label for="prediction-ticker" class="form-label">Select Cryptocurrency</label>
                                        <div class="input-group">
                                            <span class="input-group-text">
                                                <i class="fab fa-bitcoin"></i>
                                            </span>
                                            <select id="prediction-ticker" class="form-select">
                                                <option value="BTC">Bitcoin (BTC)</option>
                                                <option value="ETH">Ethereum (ETH)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="col-md-6 d-flex align-items-end">
                                        <button type="submit" class="btn btn-primary w-100 btn-lg">
                                            <i class="fas fa-magic me-2"></i>Generate Prediction
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-12">
                    <div class="card prediction-card">
                        <div class="card-header bg-gradient">
                            <h5 class="mb-0">
                                <i class="fas fa-chart-pie me-2"></i>Latest Prediction
                            </h5>
                        </div>
                        <div class="card-body">
                            <div id="loading-spinner" class="loading-spinner d-none">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Analyzing market data...</p>
                            </div>
                            <div id="prediction-result" class="d-none">
                                <div id="prediction-details"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header bg-gradient">
                            <h5 class="mb-0">
                                <i class="fas fa-history me-2"></i>Prediction History
                            </h5>
                        </div>
                        <div class="card-body">
                            <div id="history-list"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>'''
    
    # Replace the prediction section
    new_content = content[:start_index] + new_prediction_section + content[end_index:]
    
    with open("frontend/index.html", "w") as file:
        file.write(new_content)
    
    print("Updated prediction section with modern design")

if __name__ == "__main__":
    update_prediction_section()
