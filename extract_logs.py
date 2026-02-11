import os
log_path = '/home/santiagomiguelcruz/trading-bot/backend.log'
output_path = '/home/santiagomiguelcruz/trading-bot/debug_logs.txt'

if os.path.exists(log_path):
    with open(log_path, 'r') as f:
        lines = f.readlines()
        with open(output_path, 'w') as out:
            out.writelines(lines[-500:])
    print(f"Extracted {len(lines[-500:])} lines to {output_path}")
else:
    print(f"Log file not found at {log_path}")
