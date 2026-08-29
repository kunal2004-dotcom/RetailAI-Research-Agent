import glob

llm_files = [
    'backend/app/ai/nodes/planner.py',
    'backend/app/ai/nodes/evidence.py',
    'backend/app/ai/nodes/findings.py',
    'backend/app/ai/nodes/recommendations.py'
]

for file in llm_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace(
        'llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=settings.gemini_api_key)', 
        'llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", google_api_key=settings.gemini_api_key, max_retries=10)'
    )
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Updated {file}')
