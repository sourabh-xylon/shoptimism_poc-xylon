from langchain_google_vertexai import ChatVertexAI
import os
from google.oauth2 import service_account

def get_configured_llm():
    """Get LLM with proper credentials"""

    try:

        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "my-vertex-ai-app")
        
        if credentials_path:
           
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=[
                    'https://www.googleapis.com/auth/cloud-platform',
                    'https://www.googleapis.com/auth/vertex-ai'
                ]
            )
            
            return ChatVertexAI(
                model="gemini-2.5-flash",  
                temperature=0.5,
                max_tokens=None,
                max_retries=3,
                project=project_id,
                location="us-central1",
                credentials=credentials  
            )
        else:
            # Fallback to default credentials (for local development)
            return ChatVertexAI(
                model="gemini-2.5-flash",
                temperature=0.5,
                max_tokens=None,
                max_retries=3,
                project=project_id,
                location="us-central1"
            )
    except Exception as e:
        return {"message": "Error configuring LLM", "error": str(e)}

llm = get_configured_llm()

