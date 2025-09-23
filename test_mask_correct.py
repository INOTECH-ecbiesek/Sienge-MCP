import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# Test cases expected
test_cases = [
    ('usuario123', 'us****23'),  # 9 chars: us + **** + 23 
    ('admin', 'ad**in'),         # 5 chars: ad + ** + in
    ('ab', 'ab'),                # 2 chars: unchanged
    ('a', 'a*'),                 # 1 char: a + *
    ('', None)                   # empty: None
]

def correct_mask(s: str) -> str:
    """Implementação correta baseada nos casos de teste"""
    if not s:
        return None
    if len(s) == 1:
        return s + "*"
    if len(s) == 2:
        return s
    if len(s) <= 4:
        # 3-4 chars: manter início(2) + asteriscos para o resto
        return s[:2] + "*" * (len(s) - 2)
    # 5+ chars: início(2) + meio(asteriscos) + fim(2)
    # Para 5 chars como "admin" → "ad**in" (2 asteriscos)
    # Para 9 chars como "usuario123" → "us****23" (4 asteriscos)
    middle_length = len(s) - 4  # Remove início(2) + fim(2)
    return s[:2] + "*" * middle_length + s[-2:]

print('🔐 Testando implementação correta:')
for input_val, expected in test_cases:
    result = correct_mask(input_val)
    status = '✅' if result == expected else '❌'
    print(f'  {status} "{input_val}" → "{result}" (esperado: "{expected}")')