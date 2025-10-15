"""Verify TraceMind installation and setup."""
import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)

def check_file(path, description):
    """Check if file exists."""
    if Path(path).exists():
        print(f"  ✅ {description}")
        return True
    else:
        print(f"  ❌ {description} - NOT FOUND")
        return False

def check_python_packages():
    """Check if required Python packages are installed."""
    packages = [
        'fastapi', 'uvicorn', 'chromadb', 'sentence_transformers',
        'numpy', 'sklearn', 'umap', 'pydantic', 'apscheduler', 'pytest'
    ]
    
    all_installed = True
    for package in packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - NOT INSTALLED")
            all_installed = False
    
    return all_installed

def main():
    """Run verification checks."""
    print_header("TraceMind Installation Verification")
    
    # Check project structure
    print_header("Project Structure")
    
    checks = [
        ("backend/app/main.py", "Backend main application"),
        ("backend/app/api/routes.py", "API routes"),
        ("backend/app/services/embeddings.py", "Embeddings service"),
        ("backend/app/services/chroma_client.py", "ChromaDB client"),
        ("backend/app/services/compaction.py", "Compaction service"),
        ("backend/requirements.txt", "Python requirements"),
        ("frontend/package.json", "Frontend package.json"),
        ("frontend/src/App.jsx", "Frontend App component"),
        ("frontend/src/pages/Remember.jsx", "Remember page"),
        ("frontend/src/pages/Recall.jsx", "Recall page"),
        ("frontend/src/pages/Dashboard.jsx", "Dashboard page"),
        ("scripts/populate_demo.py", "Demo script"),
        ("docker-compose.yml", "Docker Compose config"),
        ("README.md", "README documentation"),
    ]
    
    structure_ok = all(check_file(path, desc) for path, desc in checks)
    
    # Check Python packages
    print_header("Python Packages")
    packages_ok = check_python_packages()
    
    # Check Node modules (if installed)
    print_header("Frontend Dependencies")
    if Path("frontend/node_modules").exists():
        print("  ✅ node_modules installed")
        node_ok = True
    else:
        print("  ⚠️  node_modules not found (run 'npm install' in frontend/)")
        node_ok = False
    
    # Summary
    print_header("Verification Summary")
    
    if structure_ok and packages_ok:
        print("  ✅ All core files present")
        print("  ✅ All Python packages installed")
        if node_ok:
            print("  ✅ Frontend dependencies installed")
        else:
            print("  ⚠️  Frontend dependencies not installed")
        
        print("\n  🎉 TraceMind is ready to run!")
        print("\n  Next steps:")
        print("     1. cd backend && python -m uvicorn app.main:app --reload")
        print("     2. cd frontend && npm run dev")
        print("     3. cd scripts && python populate_demo.py")
        print("     4. Open http://localhost:3000")
    else:
        print("  ❌ Some components are missing")
        print("\n  Please check the errors above and:")
        if not packages_ok:
            print("     - Run: cd backend && pip install -r requirements.txt")
        if not node_ok:
            print("     - Run: cd frontend && npm install")
    
    print()

if __name__ == "__main__":
    main()
