debagging = False

def debug(text):
    if debagging:
        print(f'-'*70)
        print(text)
        print(f'-'*70)