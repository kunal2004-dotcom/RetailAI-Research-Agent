import re

llm_files = [
    'backend/app/ai/nodes/planner.py',
    'backend/app/ai/nodes/evidence.py',
    'backend/app/ai/nodes/findings.py',
    'backend/app/ai/nodes/recommendations.py'
]

for file in llm_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # The broken block looks like:
    """
            import time
        from google.api_core.exceptions import ResourceExhausted

        for attempt in range(5):
            try:
                result = structured_llm.invoke(prompt)
                break
            except Exception as e:
                if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
                    import re
                    match = re.search(r'retry in ([\d\.]+)s', str(e))
                    sleep_time = float(match.group(1)) + 1.0 if match else 20.0
                    if attempt < 4:
                        logger.warning(f'Rate limit hit, sleeping for {sleep_time}s... (Attempt {attempt+1})')
                        time.sleep(sleep_time)
                    else:
                        raise
                else:
                    raise
    """
    
    # Let's find "import time" and normalize the indentation of the block below it.
    
    # We will just manually fix the indentation of that specific block
    def fix_indent(match):
        base_indent = match.group(1)
        fixed = f"""{base_indent}import time
{base_indent}from google.api_core.exceptions import ResourceExhausted
{base_indent}for attempt in range(5):
{base_indent}    try:
{base_indent}        result = structured_llm.invoke(prompt)
{base_indent}        break
{base_indent}    except Exception as e:
{base_indent}        if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
{base_indent}            import re as _re
{base_indent}            match = _re.search(r'retry in ([\\d\\.]+)s', str(e))
{base_indent}            sleep_time = float(match.group(1)) + 1.0 if match else 20.0
{base_indent}            if attempt < 4:
{base_indent}                logger.warning(f'Rate limit hit, sleeping for {{sleep_time}}s... (Attempt {{attempt+1}})')
{base_indent}                time.sleep(sleep_time)
{base_indent}            else:
{base_indent}                raise
{base_indent}        else:
{base_indent}            raise"""
        return fixed

    # Regex to find the broken block
    pattern = r"([ \t]*)import time\s*from google\.api_core\.exceptions import ResourceExhausted\s*for attempt in range\(5\):.*?else:\s*raise"
    
    content = re.sub(pattern, fix_indent, content, flags=re.DOTALL)
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Fixed {file}')

