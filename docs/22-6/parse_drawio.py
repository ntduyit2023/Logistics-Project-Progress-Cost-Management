import re
with open(r'E:\University\Year 3-3\DA3\docs\22-6\ERD.drawio', 'r', encoding='utf-8') as f:
    content = f.read()
    
values = re.findall(r'value="(.*?)"', content)
for v in values:
    v = v.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '\"').replace('&amp;', '&')
    v = re.sub(r'<br\s*/?>', ' ', v)
    v = re.sub(r'<.*?>', '', v)
    if len(v.strip()) > 0 and len(v) < 100:
        print(v.strip())
