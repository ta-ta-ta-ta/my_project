#!/usr/bin/env python3
import sys

def main():
    # read stdin but ignore for this mock
    try:
        _ = sys.stdin.read()
    except Exception:
        pass
    # Emit a simple unified diff between PATCH_START and PATCH_END
    patch = """
PATCH_START
diff --git a/hello.txt b/hello.txt
index 0000000..e69de29
--- a/hello.txt
+++ b/hello.txt
@@
+Hello from mock LLM
PATCH_END
"""
    sys.stdout.write(patch)

if __name__ == '__main__':
    main()
