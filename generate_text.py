import requests

EDEN_AI_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNzc5NmQ0M2UtN2M0MS00YmZjLTlmMTEtYzVmMTllOGNhODQzIiwidHlwZSI6ImFwaV90b2tlbiJ9.fNbGuzFXtSPih7LNOvRFZAFxqE53f_zkWKEifbAzSs4"

def generate_summary(job_desc):
    url = "https://api.edenai.run/v2/multimodal/chat"
    
    payload = {
        "response_as_dict": True,
        "attributes_as_list": False,
        "show_base_64": True,
        "show_original_response": True,
        "temperature": 0.7,
        "max_tokens": 200,
        "providers": ["openai/gpt-4-turbo"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "content": {
                            "text": f"Generate a concise professional summary for a resume based on this job description: {job_desc}"
                        }
                    }
                ]
            }
        ]
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {EDEN_AI_API_KEY}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response_json = response.json()
    
    # Extract the summary from the generated_text field
    generated_summary = response_json.get("openai/gpt-4-turbo", {}).get("generated_text", "")
    
    return generated_summary
