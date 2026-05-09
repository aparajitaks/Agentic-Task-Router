import ast
import os

def check_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"{filepath}:{e.lineno}:{e.offset}: {e.msg}"
    except Exception as e:
        return False, f"{filepath}: {str(e)}"

def main():
    errors = []
    for root, dirs, files in os.walk('backend/app'):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                ok, err = check_file(path)
                if not ok:
                    errors.append(err)
    
    if errors:
        print("\n".join(errors))
    else:
        print("No syntax errors found.")

if __name__ == "__main__":
    main()
