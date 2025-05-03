import streamlit as st
import base64
import hashlib
from datetime import datetime
import os

def local_css(file_name):
    """Load and apply local CSS"""
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
def get_image_as_base64(path):
    """Convert an image to base64 string for embedding in CSS/HTML"""
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def hash_password(password):
    """Hash a password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_account(username, email, password, full_name):
    """Create a user account in the database"""
    # This would normally connect to a user database
    # For now we'll just store in session state
    if 'user_accounts' not in st.session_state:
        st.session_state.user_accounts = {}
        
    if username in st.session_state.user_accounts:
        return False, "Username already exists"
    
    # Create user account
    st.session_state.user_accounts[username] = {
        'email': email,
        'password': hash_password(password),  # Hash the password
        'full_name': full_name,
        'created_at': datetime.now(),
        'has_demat': False
    }
    
    return True, "Account created successfully"

def login(username, password):
    """Login a user"""
    if 'user_accounts' not in st.session_state:
        return False, "Invalid username or password"
    
    if username not in st.session_state.user_accounts:
        return False, "Invalid username or password"
    
    user = st.session_state.user_accounts[username]
    if user['password'] != hash_password(password):
        return False, "Invalid username or password"
    
    # Set logged in user
    st.session_state.logged_in = True
    st.session_state.current_user = username
    
    return True, "Login successful"

def logout():
    """Logout the current user"""
    st.session_state.logged_in = False
    if 'current_user' in st.session_state:
        del st.session_state.current_user

def is_logged_in():
    """Check if a user is logged in"""
    return st.session_state.get('logged_in', False)

def get_current_user():
    """Get the currently logged in user"""
    if not is_logged_in():
        return None
    
    username = st.session_state.get('current_user')
    if not username:
        return None
    
    return st.session_state.user_accounts.get(username)

def set_demat_account(demat_id):
    """Set the demat account ID for the current user"""
    if not is_logged_in():
        return False, "You must be logged in to set a demat account"
    
    username = st.session_state.get('current_user')
    if not username:
        return False, "User not found"
    
    st.session_state.user_accounts[username]['has_demat'] = True
    st.session_state.user_accounts[username]['demat_id'] = demat_id
    
    return True, "Demat account connected successfully"

def has_demat_account():
    """Check if the current user has a demat account"""
    user = get_current_user()
    if not user:
        return False
    
    return user.get('has_demat', False)

def add_to_watchlist(user, ticker):
    """Add a stock ticker to the user's watchlist"""
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = {}

    if user not in st.session_state.watchlist:
        st.session_state.watchlist[user] = []

    if ticker not in st.session_state.watchlist[user]:
        st.session_state.watchlist[user].append(ticker)
        return True, f"{ticker} added to your watchlist."
    return False, f"{ticker} is already in your watchlist."

def remove_from_watchlist(user, ticker):
    """Remove a stock ticker from the user's watchlist"""
    if 'watchlist' in st.session_state and user in st.session_state.watchlist:
        if ticker in st.session_state.watchlist[user]:
            st.session_state.watchlist[user].remove(ticker)
            return True, f"{ticker} removed from your watchlist."
    return False, f"{ticker} is not in your watchlist."

def send_email_notification(to_email, subject, body):
    """Send email notifications to users"""
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import smtplib
        
        # Email configuration (replace with your SMTP settings)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASSWORD")
        
        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = subject
        
        # Add body
        message.attach(MIMEText(body, "html"))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def send_price_alert(user_email, ticker, price, alert_type="target"):
    """Send price alert email"""
    subject = f"Price Alert: {ticker}"
    body = f"""
    <html>
        <body>
            <h2>Stock Price Alert</h2>
            <p>Your {alert_type} price for {ticker} has been reached!</p>
            <p>Current Price: ${price:.2f}</p>
            <p>Login to your account to view more details.</p>
        </body>
    </html>
    """
    return send_email_notification(user_email, subject, body)

def send_weekly_summary(user_email, portfolio_data):
    """Send weekly portfolio summary"""
    total_value = portfolio_data['total_value']
    weekly_change = portfolio_data['weekly_change']
    top_performers = portfolio_data['top_performers']
    
    subject = "Your Weekly Portfolio Summary"
    body = f"""
    <html>
        <body>
            <h2>Weekly Portfolio Summary</h2>
            <p>Total Portfolio Value: ${total_value:,.2f}</p>
            <p>Weekly Change: {weekly_change:+.2f}%</p>
            
            <h3>Top Performers</h3>
            <ul>
                {"".join([f"<li>{stock}: {change:+.2f}%</li>" for stock, change in top_performers])}
            </ul>
            
            <p>Login to your account for detailed analysis.</p>
        </body>
    </html>
    """
    return send_email_notification(user_email, subject, body)

def show_app_features():
    """Display the main features of the app"""
    st.markdown("""
    <div class="feature-section">
        <h2>Welcome to StockSmart</h2>
        <p>Your all-in-one platform for stock analysis, trading simulation, and portfolio management</p>
        
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon-container">
                    <img src="./assets/real_time.png" class="feature-icon" alt="Real-Time Analysis">
                </div>
                <h3>Real-Time Analysis</h3>
                <p>Access real-time stock data and advanced technical indicators like RSI to make informed decisions.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon-container">
                    <img src="./assets/trading.png" class="feature-icon" alt="Trading Recommendations">
                </div>
                <h3>Trading Recommendations</h3>
                <p>Get AI-powered buy, sell, or hold recommendations based on technical analysis.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon-container">
                    <img src="./assets/portfolio.png" class="feature-icon" alt="Portfolio Management">
                </div>
                <h3>Portfolio Management</h3>
                <p>Track your investments, monitor performance, and analyze profit/loss in real-time.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon-container">
                    <img src="./assets/simulation.png" class="feature-icon" alt="Risk-Free Simulation">
                </div>
                <h3>Risk-Free Simulation</h3>
                <p>Practice trading strategies without risking real money using our advanced simulator.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon-container">
                    <img src="./assets/analytics.png" class="feature-icon" alt="Interactive Charts">
                </div>
                <h3>Interactive Charts</h3>
                <p>Visualize stock performance with customizable, interactive charts and indicators.</p>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon-container">
                    <img src="./assets/storage.png" class="feature-icon" alt="Persistent Storage">
                </div>
                <h3>Persistent Storage</h3>
                <p>Your portfolio and transaction history are securely stored and available anytime.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
def show_login_signup():
    """Show the login and signup options"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="auth-card">
            <h3>Sign In</h3>
            <p>Access your portfolio and continue your trading journey</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
        st.markdown("""
        <div class="auth-card">
            <h3>Create Account</h3>
            <p>Join thousands of traders and start your investment journey today</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("signup_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Create Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submit_button = st.form_submit_button("Create Account")
            
            if submit_button:
                if not (full_name and email and new_username and new_password and confirm_password):
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                else:
                    success, message = create_user_account(new_username, email, new_password, full_name)
                    if success:
                        st.success(message)
                        success, _ = login(new_username, new_password)
                        if success:
                            st.rerun()
                    else:
                        st.error(message)

def show_demat_connection():
    """Show the demat account connection option"""
    st.markdown("""
    <div class="demat-section">
        <h3>Connect Your Demat Account</h3>
        <p>Link your existing demat account to trade with real money or create a new one</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="demat-card">
            <h4>Connect Existing Account</h4>
            <p>Link your broker account to access real trading</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("connect_demat"):
            broker = st.selectbox("Select Broker", ["Zerodha", "Upstox", "Angel One", "ICICI Direct", "HDFC Securities"])
            demat_id = st.text_input("Demat Account ID")
            
            submit_button = st.form_submit_button("Connect Account")
            
            if submit_button:
                if demat_id:
                    success, message = set_demat_account(demat_id)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter your Demat Account ID")
    
    with col2:
        st.markdown("""
        <div class="demat-card">
            <h4>Open New Demat Account</h4>
            <p>Don't have a demat account? Open one with our partner brokers</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="broker-options">
            <p>Choose a broker to open a new account:</p>
            <ul>
                <li>Zerodha - Commission-free trading, easy to use</li>
                <li>Upstox - Low brokerage, advanced tools</li>
                <li>Angel One - Comprehensive research, good for beginners</li>
            </ul>
            <p class="note">Note: This will redirect you to the broker's website</p>
        </div>
        """, unsafe_allow_html=True)
        
        broker_choice = st.selectbox("Select Preferred Broker", ["Zerodha", "Upstox", "Angel One"])
        
        if st.button("Open New Account"):
            st.info(f"This would redirect to {broker_choice}'s account opening page in a real application.")
            st.markdown(f"[Visit {broker_choice} Website](https://www.{broker_choice.lower().replace(' ', '')}.com)")

def user_profile_sidebar():
    """Show user profile in sidebar"""
    if is_logged_in():
        user = get_current_user()
        st.sidebar.markdown(f"""
        <div class="user-profile">
            <img src="/app/images/avatar.png" class="avatar-img" alt="User Avatar" style="width: 50px; height: 50px; border-radius: 50%; margin-right: 10px;">
            <div class="user-info">
                <h4>{user['full_name']}</h4>
                <p>{user['email']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if user.get('has_demat', False):
            st.sidebar.markdown("""
            <div class="account-status connected">
                <span><img src="/app/images/feature3.png" style="width: 15px; height: 15px; margin-right: 5px;"> Demat Connected</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.sidebar.markdown("""
            <div class="account-status">
                <span><img src="/app/images/feature4.png" style="width: 15px; height: 15px; margin-right: 5px;"> Demat Not Connected</span>
            </div>
            """, unsafe_allow_html=True)
        
        if st.sidebar.button("Logout"):
            logout()
            st.rerun()