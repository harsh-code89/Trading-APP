import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime, timedelta
import time
import pickle
import utils
import yfinance as yf
import db
from PIL import Image

# Initialize database before setting up the app
if not db.init_database():
    st.error("Failed to initialize database. Some features may not work properly.")

# Set page title and configuration
st.set_page_config(
    page_title="StockSmart - Trading & Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session states
if "account_created" not in st.session_state:
    st.session_state.account_created = False

# Load and apply custom CSS
with open("styles/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.image("assets/logo.png", width=100)
    st.title("StockSmart")
    
    if st.session_state.account_created:
        st.subheader("Navigation")
        
        # Main Features
        st.markdown("### 📊 Analysis")
        if st.sidebar.button("Market Analysis", use_container_width=True):
            st.switch_page("pages/real_time.py")
        if st.sidebar.button("Technical Analysis", use_container_width=True):
            st.switch_page("pages/technical_analysis.py")
        if st.sidebar.button("Stock Screener", use_container_width=True):
            st.switch_page("pages/screener.py")
            
        st.markdown("### 💹 Trading")
        if st.sidebar.button("Trade Stocks", use_container_width=True):
            st.switch_page("pages/trading.py")
        if st.sidebar.button("Trading Simulator", use_container_width=True):
            st.switch_page("pages/simulation.py")
            
        st.markdown("### 📈 Portfolio")
        if st.sidebar.button("My Portfolio", use_container_width=True):
            st.switch_page("pages/portfolio.py")
        if st.sidebar.button("Watchlist", use_container_width=True):
            st.switch_page("pages/watchlist.py")
            
        st.markdown("### 👥 Community")
        if st.sidebar.button("Trading Community", use_container_width=True):
            st.switch_page("pages/8_social.py")
            
        st.markdown("### 🔔 Notifications")
        if st.sidebar.button("Alert Center", use_container_width=True):
            st.switch_page("pages/notifications.py")
        
        # User profile section at bottom of sidebar
        st.markdown("---")
        st.markdown("### 👤 Account")
        if st.sidebar.button("Logout"):
            st.session_state.account_created = False
            st.rerun()
    else:
        st.info("Please login to access all features")

# Header Section
col1, col2 = st.columns([1, 5])
with col1:
    st.image("assets/logo.png", width=100)
with col2:
    st.title("StockSmart")
    st.subheader("Your Smart Trading Companion")

# If not logged in, show landing page
if not st.session_state.account_created:
    st.markdown("---")
    
    # Hero Section with improved layout
    st.header("Start Your Trading Journey")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Welcome to StockSmart")
        st.write("Your all-in-one platform for stock analysis, trading simulation, and portfolio management.")
        
        # Login Form
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted and email and password:
                # Here you would typically validate credentials
                st.session_state.account_created = True
                st.rerun()
    
    with col2:
        st.image("images/trading_bg.jpg", use_column_width=True)
    
    # Features Section with improved layout
    st.markdown("---")
    st.header("Features")
    
    # First row of features
    with st.container():
        col1, col2, col3 = st.columns([1, 1, 1], gap="large")
        
        with col1:
            st.image("assets/real_time.png", use_column_width=True)
            st.subheader("Real-Time Analysis")
            st.write("Access real-time market data and advanced technical indicators.")
        
        with col2:
            st.image("assets/trading.png", use_column_width=True)
            st.subheader("Smart Trading")
            st.write("Get AI-powered trading recommendations and signals.")
        
        with col3:
            st.image("assets/portfolio.png", use_column_width=True)
            st.subheader("Portfolio Management")
            st.write("Track and analyze your investments in real-time.")
    
    # Second row of features
    with st.container():
        col1, col2, col3 = st.columns([1, 1, 1], gap="large")
        
        with col1:
            st.image("assets/simulation.png", use_column_width=True)
            st.subheader("Risk-Free Practice")
            st.write("Test your strategies with our trading simulator.")
        
        with col2:
            st.image("images/feature5.png", use_column_width=True)
            st.subheader("Advanced Analytics")
            st.write("Deep insights with technical and fundamental analysis.")
        
        with col3:
            st.image("images/feature6.png", use_column_width=True)
            st.subheader("Community Trading")
            st.write("Connect with traders and share insights.")

else:
    # Main Dashboard
    st.markdown("---")
    
    # Quick Actions
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.image("assets/real_time.png", width=60)
        st.subheader("Market Analysis")
        if st.button("Open Analysis"):
            try:
                st.switch_page("pages/real_time.py")
            except Exception as e:
                st.error("Unable to load Market Analysis. Please try again.")
    
    with col2:
        st.image("assets/trading.png", width=60)
        st.subheader("Trade Stocks")
        if st.button("Start Trading"):
            try:
                st.switch_page("pages/trading.py")
            except Exception as e:
                st.error("Unable to load Trading page. Please try again.")
    
    with col3:
        st.image("assets/simulation.png", width=60)
        st.subheader("Simulator")
        if st.button("Try Simulator"):
            try:
                st.switch_page("pages/simulation.py")
            except Exception as e:
                st.error("Unable to load Simulator. Please try again.")
    
    with col4:
        st.image("assets/portfolio.png", width=60)
        st.subheader("Portfolio")
        if st.button("View Portfolio"):
            try:
                st.switch_page("pages/portfolio.py")
            except Exception as e:
                st.error("Unable to load Portfolio. Please try again.")
    
    # Market Overview
    st.markdown("---")
    st.subheader("Market Overview")

    # Get market data with optimized caching
    try:
        indices = ['^GSPC', '^DJI', '^IXIC']  # S&P 500, Dow Jones, NASDAQ
        market_data = []
        
        # Create a batch request for all indices
        for index in indices:
            cache_key = f"market_index_{index}_{datetime.now().strftime('%Y%m%d')}"
            cache_file = os.path.join('cache', f"{cache_key}.pkl")
            
            try:
                # Check for cached data less than 5 minutes old
                if os.path.exists(cache_file):
                    modified_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
                    if datetime.now() - modified_time < timedelta(minutes=5):
                        with open(cache_file, 'rb') as f:
                            data = pickle.load(f)
                            market_data.append(data)
                            continue
                
                # If no valid cache, fetch new data
                ticker = yf.Ticker(index)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Open'].iloc[0]
                    change = ((current - prev) / prev) * 100
                    data = {
                        'Index': index.replace('^', ''),
                        'Price': current,
                        'Change': change
                    }
                    market_data.append(data)
                    
                    # Cache the new data
                    os.makedirs('cache', exist_ok=True)
                    with open(cache_file, 'wb') as f:
                        pickle.dump(data, f)
                    
            except Exception as e:
                st.warning(f"Unable to fetch data for {index}")
                continue
        
        # Display market data with enhanced styling
        if market_data:
            col1, col2, col3 = st.columns(3)
            for idx, data in enumerate(market_data):
                with [col1, col2, col3][idx]:
                    delta_color = "normal" if data['Change'] == 0 else ("inverse" if data['Change'] < 0 else "increase")
                    st.metric(
                        data['Index'],
                        f"${data['Price']:,.2f}",
                        f"{data['Change']:.2f}%",
                        delta_color=delta_color
                    )
        else:
            st.warning("No market data available. Please try again later.")
    except Exception as e:
        st.error("Unable to fetch market data. Please try again later.")

    # Recent Activity
    st.markdown("---")
    st.subheader("Recent Activity")
    
    # Display recent transactions if available
    if hasattr(st.session_state, 'transaction_history') and st.session_state.transaction_history:
        df = pd.DataFrame(st.session_state.transaction_history[-5:])  # Show last 5 transactions
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recent activity to display.")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**StockSmart**")
    st.write("Your trusted trading companion")
with col2:
    st.markdown("**Quick Links**")
    st.write("[Documentation](#)")
    st.write("[Support](#)")
with col3:
    st.markdown("**Contact**")
    st.write("support@stocksmart.com")
    st.write("© 2025 StockSmart")