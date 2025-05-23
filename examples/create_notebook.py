import re
import nbformat as nbf

def parse_python_file(file_path):
    """Parse Python file with cell markers into notebook cells."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Initialize notebook
    nb = nbf.v4.new_notebook()
    cells = []
    
    # Split content by cell markers
    cell_pattern = r'# %%(?:\s*\[markdown\])?\n(.*?)(?=# %%|$)'
    matches = re.finditer(cell_pattern, content, re.DOTALL)
    
    # Process the initial docstring if present
    docstring_match = re.match(r'"""(.*?)"""', content, re.DOTALL)
    if docstring_match:
        docstring_content = docstring_match.group(1).strip()
        cells.append(nbf.v4.new_markdown_cell(docstring_content))
    
    for match in matches:
        cell_content = match.group(1).strip()
        
        # Check if it's a markdown cell
        if match.group(0).startswith('# %% [markdown]'):
            # Process markdown format (remove leading # in each line)
            markdown_content = re.sub(r'^# ', '', cell_content, flags=re.MULTILINE)
            cells.append(nbf.v4.new_markdown_cell(markdown_content))
        else:
            # It's a code cell
            cells.append(nbf.v4.new_code_cell(cell_content))
    
    nb.cells = cells
    return nb

def main():
    """Main function to create notebook."""
    # Parse the tutorial Python file
    nb = parse_python_file('prolabdep/examples/tutorial.py')
    
    # Write the notebook
    with open('prolabdep/examples/tutorial.ipynb', 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
    
    print("Notebook created successfully!")

if __name__ == "__main__":
    main() 