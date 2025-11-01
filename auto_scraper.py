"""
Auto Scraper for NSDL FPI Data
File: auto_scraper.py
"""

import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import re

# NSDL website URL where reports are listed
NSDL_URL = "https://www.fpi.nsdl.co.in/web/Reports/FPI_Fortnightly_Selection.aspx"

# Folder to save the downloaded reports
SAVE_FOLDER = "FPI_Reports"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Headers to mimic a real browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_latest_date_from_csv():
    """Get the latest date from existing CSV files."""
    try:
        ohlc_df = pd.read_csv("Fortnightly_Sector_Indices.csv")
        ohlc_df['date'] = pd.to_datetime(ohlc_df['date'])
        latest_ohlc = ohlc_df['date'].max()
        
        fpi_df = pd.read_csv("Updated_FPI_Data_Formatted.csv")
        fpi_df['Date'] = pd.to_datetime(fpi_df['Date'], format='%d-%b-%y', errors='coerce')
        latest_fpi = fpi_df['Date'].max()
        
        return max(latest_ohlc, latest_fpi)
    except Exception as e:
        print(f"Error reading existing CSV: {e}")
        return None

def get_report_links():
    """Scrape NSDL website to get links to all available reports."""
    print(f"Accessing NSDL website at {datetime.now()}")
    try:
        response = requests.get(NSDL_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing NSDL website: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all links that lead to downloadable reports
    report_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "download" in href.lower() or ".xls" in href or ".csv" in href or "report" in href.lower():
            full_url = f"https://www.fpi.nsdl.co.in{href}" if href.startswith("/") else href
            report_links.append(full_url)
    
    print(f"✓ Found {len(report_links)} potential report links")
    return report_links

def download_new_reports(report_links, latest_date):
    """Download only new reports (after latest_date)."""
    new_downloads = 0
    
    for url in report_links:
        file_name = url.split("/")[-1]
        save_path = os.path.join(SAVE_FOLDER, file_name)
        
        # Extract date from filename if possible
        date_match = re.search(r'(\d{2}[-_]\w{3}[-_]\d{2,4})', file_name)
        if date_match and latest_date:
            try:
                file_date = pd.to_datetime(date_match.group(1), format='%d-%b-%y', errors='coerce')
                if pd.notna(file_date) and file_date <= latest_date:
                    print(f"⊘ Skipping {file_name} (older than {latest_date.date()})")
                    continue
            except:
                pass
        
        if os.path.exists(save_path):
            print(f"⊘ Skipping {file_name} (already exists)")
            continue
        
        print(f"⬇ Downloading {file_name}...")
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            
            with open(save_path, "wb") as file:
                file.write(response.content)
            print(f"✓ Saved: {file_name}")
            new_downloads += 1
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to download {file_name}: {e}")
    
    return new_downloads

def process_and_update_reports():
    """Process downloaded reports and update existing CSV files."""
    print("\n📊 Processing downloaded reports...")
    
    all_ohlc_data = []
    all_fpi_data = []
    
    for file in os.listdir(SAVE_FOLDER):
        file_path = os.path.join(SAVE_FOLDER, file)
        try:
            # Read file based on extension
            if file.endswith(".csv"):
                df = pd.read_csv(file_path)
            elif file.endswith((".xls", ".xlsx")):
                df = pd.read_excel(file_path)
            else:
                continue
            
            # Identify data type based on columns
            if 'open' in df.columns.str.lower().tolist() or 'high' in df.columns.str.lower().tolist():
                all_ohlc_data.append(df)
                print(f"  → Processed OHLC data from {file}")
            elif 'fpi' in df.columns.str.lower().tolist() or 'net' in df.columns.str.lower().tolist():
                all_fpi_data.append(df)
                print(f"  → Processed FPI data from {file}")
                
        except Exception as e:
            print(f"❌ Error processing {file}: {e}")
    
    # Update OHLC CSV
    if all_ohlc_data:
        try:
            existing_ohlc = pd.read_csv("Fortnightly_Sector_Indices.csv")
            new_ohlc = pd.concat(all_ohlc_data, ignore_index=True)
            combined_ohlc = pd.concat([existing_ohlc, new_ohlc], ignore_index=True)
            
            # Remove duplicates based on date and sector
            combined_ohlc['date'] = pd.to_datetime(combined_ohlc['date'], errors='coerce')
            combined_ohlc = combined_ohlc.drop_duplicates(subset=['date', 'sector'], keep='last')
            combined_ohlc = combined_ohlc.sort_values('date')
            
            combined_ohlc.to_csv("Fortnightly_Sector_Indices.csv", index=False)
            print(f"✓ Updated Fortnightly_Sector_Indices.csv ({len(new_ohlc)} new records)")
        except Exception as e:
            print(f"❌ Error updating OHLC CSV: {e}")
    
    # Update FPI CSV
    if all_fpi_data:
        try:
            existing_fpi = pd.read_csv("Updated_FPI_Data_Formatted.csv")
            new_fpi = pd.concat(all_fpi_data, ignore_index=True)
            combined_fpi = pd.concat([existing_fpi, new_fpi], ignore_index=True)
            
            # Standardize column names
            combined_fpi.columns = combined_fpi.columns.str.strip()
            if 'date' not in combined_fpi.columns and 'Date' in combined_fpi.columns:
                combined_fpi.rename(columns={'Date': 'date'}, inplace=True)
            
            # Remove duplicates
            combined_fpi['date'] = pd.to_datetime(combined_fpi['date'], errors='coerce')
            combined_fpi = combined_fpi.drop_duplicates(subset=['date', 'sector '], keep='last')
            combined_fpi = combined_fpi.sort_values('date')
            
            combined_fpi.to_csv("Updated_FPI_Data_Formatted.csv", index=False)
            print(f"✓ Updated Updated_FPI_Data_Formatted.csv ({len(new_fpi)} new records)")
        except Exception as e:
            print(f"❌ Error updating FPI CSV: {e}")
    
    return len(all_ohlc_data) > 0 or len(all_fpi_data) > 0

def main():
    """Main execution function."""
    print("=" * 60)
    print("🚀 NSDL FPI Data Auto-Update Script")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Get latest date from existing data
    latest_date = get_latest_date_from_csv()
    if latest_date:
        print(f"📅 Latest data date: {latest_date.date()}")
    else:
        print("⚠ No existing data found, will download all available reports")
    
    # Scrape for report links
    links = get_report_links()
    
    if not links:
        print("\n❌ No reports found. Exiting.")
        return
    
    # Download new reports
    print(f"\n⬇ Downloading new reports...")
    new_downloads = download_new_reports(links, latest_date)
    
    if new_downloads == 0:
        print("\n✓ No new reports to download. Data is up to date!")
        return
    
    print(f"\n✓ Downloaded {new_downloads} new report(s)")
    
    # Process and update CSVs
    updated = process_and_update_reports()
    
    if updated:
        print("\n" + "=" * 60)
        print("✅ SUCCESS! CSV files have been updated")
        print("=" * 60)
    else:
        print("\n⚠ No new data to update")

if __name__ == "__main__":
    main()