import secrets
import string

def generate_alphanumeric_key(length=16):
    """Generate a secure random key using only letters and numbers"""
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return key

# Generate values
admin_password = generate_alphanumeric_key(16)
secret_key = generate_alphanumeric_key(50)
rest_key = generate_alphanumeric_key(32)

# Print all required configuration values
print("# Admin password and secret key")
print("OTREE_ADMIN_PASSWORD=" + admin_password)
print("OTREE_SECRET_KEY=" + secret_key)
print("# Production settings")
print("OTREE_PRODUCTION=1")
print("OTREE_AUTH_LEVEL=DEMO")
print("# oTree REST API key for botex")
print("OTREE_REST_KEY=" + rest_key)
print("# LLM API key for botex")
print("OTREE_GEMINI_API_KEY=your_gemini_api_key_here")
print("# Optional configurations")
print("# OPENAI_API_KEY=your_openai_api_key_here")
print("# LLAMACPP_SERVER_PATH=/path/to/llama-cpp-server")
print("# LLAMACPP_LOCAL_LLM_PATH=/path/to/local/model")
print("# BOTEX_DB=custom_path_to_botex.sqlite3")
print("# OTREE_PROJECT_PATH=/path/to/otree/project")
print("\nAdd these to your .env file or environment variables.")