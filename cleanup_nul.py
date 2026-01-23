import os
import sys

def cleanup_ghost_files():
    # Use \\.\ prefix to access reserved filenames on Windows
    # Paths to potential ghost files based on git output: "backend/nul" and "nul"
    
    base_dir = os.getcwd()
    
    # List of relative paths to check
    targets = [
        "nul", 
        "backend\\nul", 
        "backend/nul"
    ]
    
    for rel_path in targets:
        # Construct absolute path
        abs_path = os.path.join(base_dir, rel_path)
        
        # Try normal delete first
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
                print(f"✅ Deleted (normal): {rel_path}")
                continue
            except Exception as e:
                print(f"⚠️ Failed normal delete for {rel_path}: {e}")
        
        # Try raw path for reserved names
        # Standard: \\.\C:\path\nul
        raw_path = r"\\.\"" + abs_path + r"\"" # quoting ? or just \\.\path
        # Actually in Python os.remove with \\?\ prefix often works
        
        unc_path = r"\\?\" + abs_path
        
        try:
            # os.remove might work with UNC prefix for some things but `nul` is special.
            # We can try executing 'del' via shell with special syntax
            cmd = f'del "\\\\.\\{abs_path}"'
            print(f"Running system cmd: {cmd}")
            ret = os.system(cmd)
            if ret == 0:
                print(f"✅ Deleted (system cmd): {rel_path}")
            else:
                print(f"❌ Failed system cmd for {rel_path}")
        except Exception as e:
            print(f"❌ Error handling {rel_path}: {e}")

if __name__ == "__main__":
    cleanup_ghost_files()
