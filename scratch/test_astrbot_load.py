import subprocess
import sys

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8")
    return res.returncode, res.stdout, res.stderr

def main():
    print("=== 1. Container Import Check ===")
    code, out, err = run_cmd("docker exec -w /AstrBot/data/plugins/astrbot_plugin_text_roguelike -e PYTHONPATH=/AstrBot/data/plugins/astrbot_plugin_text_roguelike astrbot-test-env python -c \"from astrbot.api.star import Star; from main import MyPlugin; print('Import check passed')\"")
    print(out)
    if code != 0 or "Import check passed" not in out:
        print(f"Import check failed with exit code {code}: {err}")
        sys.exit(1)
        
    print("=== 2. AstrBot Plugin Loading Log Check ===")
    code, out, err = run_cmd("docker logs astrbot-test-env")
    if code != 0:
        print(f"Failed to fetch container logs with exit code {code}: {err}")
        sys.exit(1)
        
    log_content = out + "\n" + err
    
    load_start_msg = "Loading plugin astrbot_plugin_text_roguelike ..."
    load_success_msg = "Plugin astrbot_plugin_text_roguelike"
    
    if load_start_msg not in log_content:
        print("Error: Plugin load start log not found in container logs.")
        sys.exit(1)
        
    if load_success_msg not in log_content:
        print("Error: Plugin load success log not found in container logs.")
        sys.exit(1)
        
    error_keywords = ["Traceback", "Exception", "Error"]
    lines = log_content.split("\n")
    for line in lines:
        if "astrbot_plugin_text_roguelike" in line:
            for keyword in error_keywords:
                if keyword in line:
                    print(f"Error log detected matching keyword '{keyword}': {line}")
                    sys.exit(1)
                    
    print("AstrBot plugin loading verification passed successfully!")

if __name__ == "__main__":
    main()
