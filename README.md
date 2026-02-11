# Render Deployment Instructions

To deploy on Render with a Python 3.11.9 backend, follow these instructions:

- Set the root directory to `backend`.
- Use the following build command:
  ```
  pip install -r requirements.txt
  ```
- Use the following start command:
  ```
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

Ensure all configurations are correctly set in your Render dashboard.