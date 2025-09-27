#!/usr/bin/env python3
"""
Production Environment Verification Script
Run this on Railway to check current storage setup
"""
import os
import logging
from pathlib import Path

def verify_production_environment():
    """Verify current production environment setup"""
    print("=== PhotoVault Production Environment Verification ===\n")
    
    # 1. Check environment variables
    print("1. Environment Variables:")
    env_vars = [
        'DATABASE_URL', 'UPLOAD_FOLDER', 'SECRET_KEY', 
        'REPL_ID', 'REPLIT_DB_URL', 'RAILWAY_ENVIRONMENT'
    ]
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        if var in ['SECRET_KEY', 'DATABASE_URL']:
            value = f"{'SET' if value != 'NOT SET' else 'NOT SET'} ({'***HIDDEN***' if value != 'NOT SET' else ''})"
        print(f"   {var}: {value}")
    
    # 2. Check upload folder configuration
    print("\n2. Upload Folder Configuration:")
    upload_folder = os.environ.get('UPLOAD_FOLDER')
    if upload_folder:
        print(f"   Configured path: {upload_folder}")
        print(f"   Path exists: {Path(upload_folder).exists()}")
        if Path(upload_folder).exists():
            try:
                files = list(Path(upload_folder).rglob('*'))
                print(f"   Total files: {len([f for f in files if f.is_file()])}")
                print(f"   Total folders: {len([f for f in files if f.is_dir()])}")
            except Exception as e:
                print(f"   Error reading folder: {e}")
    else:
        print("   Using default: photovault/uploads (relative path)")
        default_path = Path('photovault/uploads')
        print(f"   Default path exists: {default_path.exists()}")
    
    # 3. Check App Storage availability
    print("\n3. App Storage (Replit Object Storage) Status:")
    try:
        from photovault.services.app_storage_service import app_storage
        print(f"   Available: {app_storage.is_available()}")
        if not app_storage.is_available():
            print("   → Falling back to local filesystem storage")
            print("   → FILES MAY BE LOST ON CONTAINER RESTARTS!")
    except Exception as e:
        print(f"   Error checking App Storage: {e}")
    
    # 4. Check current working directory and filesystem
    print("\n4. Filesystem Information:")
    cwd = Path.cwd()
    print(f"   Current working directory: {cwd}")
    print(f"   App directory: {cwd}")
    
    # Check for existing uploads
    potential_upload_paths = [
        'photovault/uploads',
        'uploads', 
        '/app/uploads',
        '/app/data/uploads'
    ]
    
    for path in potential_upload_paths:
        p = Path(path)
        if p.exists():
            try:
                files = list(p.rglob('*.*'))
                print(f"   Found uploads in {path}: {len(files)} files")
            except Exception as e:
                print(f"   Error reading {path}: {e}")
    
    # 5. Check deployment platform
    print("\n5. Deployment Platform:")
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        print("   Platform: Railway")
        print("   → LOCAL STORAGE IS EPHEMERAL - IMPLEMENT VOLUMES OR CLOUD STORAGE!")
    elif os.environ.get('REPL_ID'):
        print("   Platform: Replit")
        print("   → Local storage should be persistent")
    else:
        print("   Platform: Unknown")
    
    print("\n=== End Verification ===")

if __name__ == "__main__":
    verify_production_environment()