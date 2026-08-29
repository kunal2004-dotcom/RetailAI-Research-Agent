import glob

# Replace LLM in planner, evidence, findings, recommendations
llm_files = [
    'backend/app/ai/nodes/planner.py',
    'backend/app/ai/nodes/evidence.py',
    'backend/app/ai/nodes/findings.py',
    'backend/app/ai/nodes/recommendations.py'
]

for file in llm_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Imports
    content = content.replace(
        'from langchain_openai import ChatOpenAI',
        'from langchain_google_genai import ChatGoogleGenerativeAI'
    )
    
    # Fallback logic
    content = content.replace(
        'if settings.openai_api_key in ["your_openai_api_key_here", "dummy"]:',
        'if settings.gemini_api_key in ["your_gemini_api_key_here", "dummy"]:'
    )
    content = content.replace(
        'No OpenAI API key found',
        'No Gemini API key found'
    )
    
    # Instantiation
    content = content.replace(
        'llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)',
        'llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=settings.gemini_api_key)'
    )
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {file}")

# Replace embeddings
embeddings_file = 'backend/app/retrieval/embeddings.py'
with open(embeddings_file, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'from langchain_openai import OpenAIEmbeddings',
    'from langchain_google_genai import GoogleGenerativeAIEmbeddings'
)
content = content.replace(
    'BaseOpenAIEmbeddings',
    'BaseGeminiEmbeddings'
)
content = content.replace(
    'self.embeddings = OpenAIEmbeddings(api_key=settings.openai_api_key)',
    'self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=settings.gemini_api_key)'
)
content = content.replace(
    'if settings.openai_api_key in ["your_openai_api_key_here", "dummy"]:',
    'if settings.gemini_api_key in ["your_gemini_api_key_here", "dummy"]:'
)
content = content.replace(
    'return BaseOpenAIEmbeddings()',
    'return BaseGeminiEmbeddings()'
)
with open(embeddings_file, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Updated {embeddings_file}")

# Replace search fallback checking
search_file = 'backend/app/retrieval/search_provider.py'
with open(search_file, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'if settings.openai_api_key not in ["your_openai_api_key_here", "dummy"]:',
    'if settings.gemini_api_key not in ["your_gemini_api_key_here", "dummy"]:'
)
with open(search_file, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Updated {search_file}")

