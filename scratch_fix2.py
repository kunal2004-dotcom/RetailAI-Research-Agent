import glob

files = glob.glob('backend/app/ai/nodes/*.py') + glob.glob('backend/app/retrieval/*.py')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    old_str1 = 'if not settings.openai_api_key or settings.openai_api_key in ["your_openai_api_key_here", "dummy"]:'
    new_str1 = 'if settings.openai_api_key in ["your_openai_api_key_here", "dummy"]:'
    
    old_str2 = 'if settings.openai_api_key and settings.openai_api_key not in ["your_openai_api_key_here", "dummy"]:'
    new_str2 = 'if settings.openai_api_key not in ["your_openai_api_key_here", "dummy"]:'
    
    if old_str1 in content or old_str2 in content:
        content = content.replace(old_str1, new_str1)
        content = content.replace(old_str2, new_str2)
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")
