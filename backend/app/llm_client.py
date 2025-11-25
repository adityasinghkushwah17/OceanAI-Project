import os
from dotenv import load_dotenv
load_dotenv()

LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'mock')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'text-bison@001')
GEMINI_ENDPOINT = os.getenv('GEMINI_ENDPOINT')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'google/gemini-2.5-flash-lite')
OPENROUTER_ENDPOINT = os.getenv('OPENROUTER_ENDPOINT')


def generate_for_section(prompt: str, context: str | None = None) -> str:
    """
    Generate text for a single section.
    If `LLM_PROVIDER=openai` and `OPENAI_API_KEY` is set, call OpenAI ChatCompletion API (gpt-3.5-turbo).
    Otherwise, return a clear mock response.
    """
    if LLM_PROVIDER == 'openai' and OPENAI_API_KEY:
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            messages = [
                {"role": "system", "content": "You are a helpful assistant that writes clear, concise, and well-structured business document content."},
                {"role": "user", "content": f"{prompt}\n\nContext:\n{context or ''}\n\nPlease produce a polished section of approximately 150-300 words, suitable for business documents. Use clear headings or bullets if requested."}
            ]
            resp = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages, max_tokens=600, temperature=0.2)
            if resp and 'choices' in resp and len(resp['choices']) > 0:
                text = resp['choices'][0]['message'].get('content', '').strip()
                return text
            return "[LLM returned no choices]"
        except Exception as e:
            return f"[LLM error: {e}]\nMock content for: {prompt[:200]}"

    # Mock behaviour: echo prompt with filler (explicitly helpful to the user)
    base = f"Generated content for: {prompt}\n"
    if context:
        base += f"(context: {context})\n"
    base += "\nThis is placeholder generated content. To enable real LLM outputs, set OPENAI_API_KEY in your `.env` and set LLM_PROVIDER=openai."
    return base


def _call_gemini(prompt: str, context: str | None = None) -> str:
    import requests, json
    # Build endpoint
    model = GEMINI_MODEL
    # support both 'text-bison@001' or 'text-bison-001' formats
    model_name = model.replace('@', '-')
    # Try v1 endpoint first (preferred), fallback to v1beta2
    if GEMINI_ENDPOINT:
        endpoint = GEMINI_ENDPOINT
    else:
        endpoint = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generate"
    headers = {'Content-Type': 'application/json'}
    # If user provided an API key we append as query param (API-key style)
    if GEMINI_API_KEY:
        if '?' in endpoint:
            endpoint = endpoint + f"&key={GEMINI_API_KEY}"
        else:
            endpoint = endpoint + f"?key={GEMINI_API_KEY}"
    # construct request body per Gemini text-bison generate API
    body = {
        "prompt": {
            "text": f"{prompt}\n\nContext:\n{context or ''}\n\nPlease respond with a polished business-style section."
        },
        "maxOutputTokens": 512,
        "temperature": 0.2
    }
    try:
        resp = requests.post(endpoint, headers=headers, data=json.dumps(body), timeout=30)
        if resp.status_code == 404 and not GEMINI_ENDPOINT:
            # try v1beta2 fallback
            endpoint2 = f"https://generativelanguage.googleapis.com/v1beta2/models/{model_name}:generate"
            if GEMINI_API_KEY:
                endpoint2 = endpoint2 + ("&key=" + GEMINI_API_KEY if "?" in endpoint2 else "?key=" + GEMINI_API_KEY)
            resp = requests.post(endpoint2, headers=headers, data=json.dumps(body), timeout=30)
        if resp.status_code != 200:
            return f"[Gemini error {resp.status_code}: {resp.text}]"
        data = resp.json()
        # text-bison returns 'candidates' list with 'content' field
        if 'candidates' in data and len(data['candidates']) > 0:
            cand = data['candidates'][0]
            if 'content' in cand:
                return cand['content'].strip()
            if 'output' in cand:
                return cand['output'].strip()
            if 'message' in cand and 'content' in cand['message']:
                return cand['message']['content'].strip()
        if 'output' in data and 'text' in data['output']:
            return data['output']['text'].strip()
        return str(data)
    except Exception as e:
        return f"[Gemini call error: {e}]"


def _call_openrouter(prompt: str, context: str | None = None) -> str:
    """Call OpenRouter chat completions. Expects OPENROUTER_API_KEY and OPENROUTER_MODEL set."""
    import requests, json
    # allow overriding the endpoint (useful if you want a proxy or different base)
    endpoint = OPENROUTER_ENDPOINT or 'https://openrouter.ai/api/v1/chat/completions'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {OPENROUTER_API_KEY}'}
    messages = [
        {"role": "system", "content": "You are a helpful assistant that writes clear, concise, and well-structured business document content."},
        {"role": "user", "content": f"{prompt}\n\nContext:\n{context or ''}\n\nPlease produce a polished section of approximately 150-300 words, suitable for business documents."}
    ]
    body = {"model": OPENROUTER_MODEL, "messages": messages, "temperature": 0.2, "max_tokens": 600}
    try:
        resp = requests.post(endpoint, headers=headers, data=json.dumps(body), timeout=30)
        if resp.status_code != 200:
            return f"[OpenRouter error {resp.status_code}: {resp.text}]"
        data = resp.json()
        # OpenRouter returns choices similar to OpenAI
        if 'choices' in data and len(data['choices']) > 0:
            msg = data['choices'][0].get('message') or data['choices'][0]
            if isinstance(msg, dict):
                return msg.get('content', '').strip() or str(data)
            return str(msg)
        return str(data)
    except Exception as e:
        return f"[OpenRouter call error: {e}]"


def generate_for_section(prompt: str, context: str | None = None) -> str:
    """
    Wrapper: route to OpenAI, Gemini, or mock depending on LLM_PROVIDER.
    """
    if LLM_PROVIDER == 'gemini' and GEMINI_API_KEY:
        return _call_gemini(prompt, context)
    if LLM_PROVIDER == 'openrouter' and OPENROUTER_API_KEY:
        return _call_openrouter(prompt, context)
    # fall back to openai or mock
    if LLM_PROVIDER == 'openai' and OPENAI_API_KEY:
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            messages = [
                {"role": "system", "content": "You are a helpful assistant that writes clear, concise, and well-structured business document content."},
                {"role": "user", "content": f"{prompt}\n\nContext:\n{context or ''}\n\nPlease produce a polished section of approximately 150-300 words, suitable for business documents. Use clear headings or bullets if requested."}
            ]
            resp = openai.ChatCompletion.create(model='gpt-3.5-turbo', messages=messages, max_tokens=600, temperature=0.2)
            if resp and 'choices' in resp and len(resp['choices']) > 0:
                text = resp['choices'][0]['message'].get('content', '').strip()
                return text
            return "[LLM returned no choices]"
        except Exception as e:
            return f"[LLM error: {e}]\nMock content for: {prompt[:200]}"

    # Mock behaviour
    base = f"Generated content for: {prompt}\n"
    if context:
        base += f"(context: {context})\n"
    base += "\nThis is placeholder generated content. To enable real LLM outputs, set the appropriate API key in your `.env` and set LLM_PROVIDER=openai or gemini."
    return base
