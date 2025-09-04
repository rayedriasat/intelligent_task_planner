import requests
import json

# Test the API endpoint
url = 'http://127.0.0.1:8000/api/tasks/completion-data/'

# Note: We need to be logged in to access this endpoint
# For testing, let's see what response we get

try:
    response = requests.get(url, params={'year': 2025})
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success', False)}")
        print(f"Total days: {data.get('total_days', 0)}")
        print(f"Total completed tasks: {data.get('total_completed_tasks', 0)}")
        
        # Show first few days with tasks
        if 'data' in data:
            days_with_tasks = [item for item in data['data'] if item['tasksCompleted'] > 0]
            print(f"Days with completed tasks: {len(days_with_tasks)}")
            for day in days_with_tasks[:5]:  # Show first 5 days with tasks
                print(f"  {day['date']}: {day['tasksCompleted']} tasks")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Request failed: {e}")