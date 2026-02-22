import streamlit as st
import yfinance as yf
import re
from datetime import datetime

# --- UI Setup ---
st.set_page_config(page_title="RIR Admin: Gap Filler", layout="centered")
st.title("🛠️ DB_History Gap Fetcher")
st.markdown("Paste your Google Sheets Audit Email below to automatically generate the copy/paste data for your **Import Historical Dividends** tool.")

# --- Text Input ---
email_text = st.text_area("Audit Email Text:", height=250)

# --- Fetch Logic ---
if st.button("Fetch Missing Data"):
    if not email_text:
        st.warning("Please paste the email text first.")
    else:
        with st.spinner("Scraping Yahoo Finance..."):
            
            # Split by the warning emoji to process each ticker
            sections = email_text.split('⚠️')
            
            if len(sections) <= 1:
                st.error("Could not find any tickers flagged with '⚠️'. Make sure you copied the whole email.")
            
            for section in sections[1:]:
                # Extract Ticker
                ticker_match = re.search(r'^\s*([A-Z]+)', section)
                if not ticker_match:
                    continue
                ticker = ticker_match.group(1)
                
                st.subheader(f"Data for {ticker}")
                
                try:
                    stock = yf.Ticker(ticker)
                    divs = stock.dividends
                    
                    if divs.empty:
                        st.info("No dividend data found on Yahoo Finance yet.")
                        continue
                        
                    # Remove timezone info for clean matching
                    divs.index = divs.index.tz_localize(None)
                    found_data = False
                    output_text = ""
                    
                    # 1. SCAN FOR "MIDDLE HOLES"
                    holes = re.findall(r'Hole found between (.*?) and (.*?)\n', section)
                    for start_str, end_str in holes:
                        try:
                            start_date = datetime.strptime(start_str.strip(), "%b %d, %Y")
                            end_date = datetime.strptime(end_str.strip(), "%b %d, %Y")
                            
                            mask = (divs.index > start_date) & (divs.index < end_date)
                            missing = divs[mask]
                            
                            for d, amt in missing.items():
                                output_text += f"{d.strftime('%b %d, %Y')}    {amt:.4f}\n"
                                found_data = True
                        except:
                            pass # Skip if date parsing fails on weird formatting
                            
                    # 2. SCAN FOR "TAIL END GAPS"
                    recent = re.search(r'RECENT GAP:.*? \((.*?)\)', section)
                    if recent:
                        try:
                            last_date = datetime.strptime(recent.group(1).strip(), "%b %d, %Y")
                            
                            mask = divs.index > last_date
                            missing = divs[mask]
                            
                            for d, amt in missing.items():
                                output_text += f"{d.strftime('%b %d, %Y')}    {amt:.4f}\n"
                                found_data = True
                        except:
                            pass
                            
                    # --- OUTPUT RESULTS ---
                    if found_data:
                        # st.code puts the output in a nice dark box with a copy button
                        st.code(output_text.strip(), language="text")
                    else:
                        st.info("Yahoo Finance doesn't have data for this specific gap yet (could be a delayed API update).")
                        
                except Exception as e:
                    st.error(f"Error fetching data for {ticker}: {e}")
