import requests

url = "http://localhost:11434/api/generate"

data = {
    "model" : "mistral",
    "prompt" : "Explain load balancing in system design",
    "stream" : False
}

response = requests.post(url, json = data)

print(response.json()["response"])