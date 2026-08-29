import glob

files = glob.glob('backend/app/ai/nodes/*.py') + glob.glob('backend/app/retrieval/*.py')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '== "your_openai_api_key_here"' in content or '!= "dummy"' in content:
        content = content.replace('== "your_openai_api_key_here"', 'in ["your_openai_api_key_here", "dummy"]')
        content = content.replace('!= "dummy"', 'not in ["your_openai_api_key_here", "dummy"]')
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")
