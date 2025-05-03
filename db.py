import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
import streamlit as st
import sqlite3
from pathlib import Path

load_dotenv()

# Get database connection info from environment variables
db_url = os.environ.get("DATABASE_URL", "sqlite:///stocktraderpro.db")

def init_database():
    """Initialize the database with required tables"""
    if db_url.startswith('sqlite'):
        conn = get_db_connection()
        if not conn:
            return False
        
        try:
            with conn:
                cursor = conn.cursor()
                # Create tables if they don't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfolios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        cash REAL NOT NULL DEFAULT 10000.00,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_stocks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id INTEGER,
                        ticker TEXT NOT NULL,
                        shares INTEGER NOT NULL,
                        avg_price REAL NOT NULL,
                        FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        portfolio_id INTEGER,
                        ticker TEXT NOT NULL,
                        action TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        price REAL NOT NULL,
                        total REAL NOT NULL,
                        transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                    )
                """)
                return True
        except Exception as e:
            st.error(f"Database initialization error: {e}")
            return False
        finally:
            conn.close()
    return True  # PostgreSQL tables should be created via migrations

def get_db_connection():
    """Create a connection to the database"""
    try:
        if db_url.startswith('sqlite'):
            db_path = db_url.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
        else:
            conn = psycopg2.connect(db_url)
            conn.autocommit = True
            return conn
    except (sqlite3.Error, psycopg2.Error) as e:
        st.error(f"Unable to connect to the database: {e}")
        return None

def get_sqlalchemy_engine():
    """Create a SQLAlchemy engine for more complex queries"""
    try:
        engine = create_engine(db_url)
        return engine
    except Exception as e:
        st.error(f"Unable to create SQLAlchemy engine: {e}")
        return None

def load_portfolio():
    """Load the user's portfolio from the database"""
    conn = get_db_connection()
    if not conn:
        return None, 10000.0, []
    
    try:
        # Get portfolio ID and cash
        with conn.cursor() as cur:
            if db_url.startswith('sqlite'):
                cur.execute("SELECT id, cash FROM portfolios WHERE user_id = 'default_user' LIMIT 1")
            else:
                cur.execute("SELECT id, cash FROM portfolios WHERE user_id = 'default_user' LIMIT 1")
            portfolio_data = cur.fetchone()
            
            if not portfolio_data:
                # Create a new portfolio if none exists
                if db_url.startswith('sqlite'):
                    cur.execute(
                        "INSERT INTO portfolios (user_id, cash) VALUES ('default_user', 10000.00)"
                    )
                    portfolio_id = cur.lastrowid
                    cash = 10000.0
                else:
                    cur.execute(
                        "INSERT INTO portfolios (user_id, cash) VALUES ('default_user', 10000.00) RETURNING id, cash"
                    )
                    portfolio_data = cur.fetchone()
                    portfolio_id = portfolio_data['id']
                    cash = float(portfolio_data['cash'])
            else:
                portfolio_id = portfolio_data['id']
                cash = float(portfolio_data['cash'])
            
            # Get portfolio stocks
            cur.execute(
                "SELECT ticker, shares, avg_price FROM portfolio_stocks WHERE portfolio_id = ?",
                (portfolio_id,)
            )
            stocks = cur.fetchall()
            
            # Get transaction history
            cur.execute(
                """
                SELECT ticker, action, quantity, price, total, transaction_date as timestamp 
                FROM transactions 
                WHERE portfolio_id = ?
                ORDER BY transaction_date DESC
                """,
                (portfolio_id,)
            )
            transactions = cur.fetchall()
            
            # Convert to the format expected by the app
            portfolio = {}
            for stock in stocks:
                portfolio[stock['ticker']] = {
                    'shares': stock['shares'],
                    'avg_price': float(stock['avg_price'])
                }
            
            transaction_history = []
            for tx in transactions:
                transaction_history.append({
                    'ticker': tx['ticker'],
                    'action': tx['action'],
                    'quantity': tx['quantity'],
                    'price': float(tx['price']),
                    'total': float(tx['total']),
                    'timestamp': tx['timestamp']
                })
            
            return portfolio, cash, transaction_history
    except Exception as e:
        st.error(f"Database error when loading portfolio: {e}")
        return {}, 10000.0, []
    finally:
        conn.close()

def save_portfolio(portfolio, cash, new_transaction=None):
    """Save the portfolio to the database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Get portfolio ID
            if db_url.startswith('sqlite'):
                cur.execute("SELECT id FROM portfolios WHERE user_id = 'default_user' LIMIT 1")
            else:
                cur.execute("SELECT id FROM portfolios WHERE user_id = 'default_user' LIMIT 1")
            result = cur.fetchone()
            
            if not result:
                # Create portfolio if it doesn't exist
                if db_url.startswith('sqlite'):
                    cur.execute(
                        "INSERT INTO portfolios (user_id, cash) VALUES ('default_user', ?)",
                        (cash,)
                    )
                    portfolio_id = cur.lastrowid
                else:
                    cur.execute(
                        "INSERT INTO portfolios (user_id, cash) VALUES ('default_user', %s) RETURNING id",
                        (cash,)
                    )
                    portfolio_id = cur.fetchone()['id']
            else:
                portfolio_id = result['id']
                # Update cash
                if db_url.startswith('sqlite'):
                    cur.execute(
                        "UPDATE portfolios SET cash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (cash, portfolio_id)
                    )
                else:
                    cur.execute(
                        "UPDATE portfolios SET cash = %s, updated_at = NOW() WHERE id = %s",
                        (cash, portfolio_id)
                    )
            
            # Update portfolio stocks - first clear existing entries
            cur.execute("DELETE FROM portfolio_stocks WHERE portfolio_id = ?", (portfolio_id,))
            
            # Insert current portfolio
            for ticker, details in portfolio.items():
                cur.execute(
                    """
                    INSERT INTO portfolio_stocks (portfolio_id, ticker, shares, avg_price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (portfolio_id, ticker, details['shares'], details['avg_price'])
                )
            
            # Add the new transaction if provided
            if new_transaction:
                cur.execute(
                    """
                    INSERT INTO transactions 
                    (portfolio_id, ticker, action, quantity, price, total)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        portfolio_id,
                        new_transaction['ticker'],
                        new_transaction['action'],
                        new_transaction['quantity'],
                        new_transaction['price'],
                        new_transaction['total']
                    )
                )
            
            return True
    except Exception as e:
        st.error(f"Database error when saving portfolio: {e}")
        return False
    finally:
        conn.close()

def reset_db_portfolio():
    """Reset the portfolio in the database to initial state"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Get portfolio ID
            if db_url.startswith('sqlite'):
                cur.execute("SELECT id FROM portfolios WHERE user_id = 'default_user' LIMIT 1")
            else:
                cur.execute("SELECT id FROM portfolios WHERE user_id = 'default_user' LIMIT 1")
            result = cur.fetchone()
            
            if result:
                portfolio_id = result[0]
                # Clear stocks
                cur.execute("DELETE FROM portfolio_stocks WHERE portfolio_id = ?", (portfolio_id,))
                # Clear transactions
                cur.execute("DELETE FROM transactions WHERE portfolio_id = ?", (portfolio_id,))
                # Reset cash
                if db_url.startswith('sqlite'):
                    cur.execute(
                        "UPDATE portfolios SET cash = 10000.00, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (portfolio_id,)
                    )
                else:
                    cur.execute(
                        "UPDATE portfolios SET cash = 10000.00, updated_at = NOW() WHERE id = %s",
                        (portfolio_id,)
                    )
            
            return True
    except Exception as e:
        st.error(f"Database error when resetting portfolio: {e}")
        return False
    finally:
        conn.close()

