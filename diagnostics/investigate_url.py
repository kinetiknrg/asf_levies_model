#!/usr/bin/env python3
"""
Investigate why config URL served wrong version
"""

import requests
from asf_levies_model import config
import os

def investigate_url():
    print("🔍 INVESTIGATING CONFIG URL vs ACTUAL DOWNLOAD")
    print("=" * 60)

    # Get the config URL
    config_url = config.get("data_sources").get("ofgem_annex_9")
    print(f"📋 Config URL:\n{config_url}")

    # Check file sizes locally
    data_dir = "inputs/data/raw/"
    print(f"\n📁 Local files:")
    for filename in os.listdir(data_dir):
        if 'annex' in filename.lower() and '9' in filename and filename.endswith('.xlsx'):
            filepath = os.path.join(data_dir, filename)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  {filename}: {size_mb:.2f}MB")

    # Test the config URL
    print(f"\n🌐 Testing config URL:")
    try:
        response = requests.head(config_url, timeout=10)
        if response.status_code == 200:
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                print(f"  Status: {response.status_code}")
                print(f"  Content-Length: {size_mb:.2f}MB")
                print(f"  Content-Type: {response.headers.get('content-type', 'Unknown')}")
            else:
                print(f"  Status: {response.status_code}")
                print(f"  No Content-Length header")
        else:
            print(f"  Status: {response.status_code}")
            print(f"  Error: {response.reason}")

        # Check for redirects
        if response.history:
            print(f"  🔄 Redirects detected:")
            for i, redirect in enumerate(response.history):
                print(f"    {i+1}. {redirect.status_code} → {redirect.url}")
            print(f"    Final: {response.url}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    investigate_url()