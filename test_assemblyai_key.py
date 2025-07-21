import requests

url = "https://api.assemblyai.com/v2/transcript"
headers = {
    "authorization": "b54d78abb6754c60a6d2be277ae1308a"
}

response = requests.get(url, headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.text)
