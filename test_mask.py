import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from sienge_mcp.server2 import _mask

test_cases = [
    ('usuario123', 'us****23'),
    ('admin', 'ad**in'), 
    ('ab', 'ab'),
    ('a', 'a*'),
    ('', None)
]

print('🔐 Testando função _mask corrigida:')
for input_val, expected in test_cases:
    result = _mask(input_val) if input_val or input_val == '' else None
    status = '✅' if result == expected else '❌'
    print(f'  {status} "{input_val}" → "{result}" (esperado: "{expected}")')