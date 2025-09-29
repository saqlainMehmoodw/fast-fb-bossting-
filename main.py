from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import logging
import sqlite3
import datetime
import json
import requests
import os
import sys
import random
import csv
import re
import urllib3
from urllib.parse import urlparse, parse_qs
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
import pickle
from pathlib import Path
import platform

# ==============================================
# COMPREHENSIVE LOGGING SETUP
# ==============================================

class AdvancedLogger:
    def __init__(self):
        self.logger = logging.getLogger('FacebookBot')
        self.logger.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File Handler
        file_handler = logging.FileHandler('facebook_bot_advanced.log', encoding='utf-8', mode='a')
        file_handler.setFormatter(formatter)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)

    def debug(self, message):
        self.logger.debug(message)

# ==============================================
# DATABASE MANAGEMENT CLASS
# ==============================================

class DatabaseManager:
    def __init__(self, db_path='facebook_bot_advanced.db'):
        self.db_path = db_path
        self.connection = None
        self.logger = AdvancedLogger()
        self.initialize_database()

    def get_connection(self):
        """Get database connection"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def initialize_database(self):
        """Comprehensive database initialization"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Main listings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    price TEXT,
                    location TEXT,
                    category TEXT,
                    condition TEXT,
                    status TEXT DEFAULT 'pending',
                    is_public BOOLEAN DEFAULT 0,
                    is_visible BOOLEAN DEFAULT 0,
                    is_featured BOOLEAN DEFAULT 0,
                    views_count INTEGER DEFAULT 0,
                    likes_count INTEGER DEFAULT 0,
                    shares_count INTEGER DEFAULT 0,
                    messages_count INTEGER DEFAULT 0,
                    performance_score REAL DEFAULT 0.0,
                    last_refreshed TIMESTAMP,
                    refresh_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')

            # Bot operations log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    operation_subtype TEXT,
                    status TEXT NOT NULL,
                    items_processed INTEGER DEFAULT 0,
                    items_successful INTEGER DEFAULT 0,
                    items_failed INTEGER DEFAULT 0,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    error_message TEXT,
                    stack_trace TEXT,
                    browser_session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')

            # Performance metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_date DATE NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    sample_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # User sessions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    logout_time TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    ip_address TEXT,
                    user_agent TEXT,
                    cookies_data TEXT
                )
            ''')

            # Settings and configuration
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bot_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    setting_type TEXT DEFAULT 'string',
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Competitor analysis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS competitor_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor_id TEXT NOT NULL,
                    item_title TEXT,
                    item_price TEXT,
                    item_condition TEXT,
                    location TEXT,
                    views_estimate INTEGER,
                    days_listed INTEGER,
                    price_comparison REAL,
                    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Initialize default settings
            self.initialize_default_settings(cursor)

            conn.commit()
            self.logger.info("✅ Advanced database setup completed successfully")

        except sqlite3.Error as e:
            self.logger.error(f"❌ Database initialization error: {e}")
            raise

    def initialize_default_settings(self, cursor):
        """Initialize default bot settings"""
        default_settings = [
            ('auto_refresh_enabled', 'true', 'boolean', 'Enable automatic listing refresh'),
            ('refresh_interval_hours', '6', 'integer', 'Hours between refreshes'),
            ('max_refresh_per_day', '4', 'integer', 'Maximum refreshes per day'),
            ('auto_login_enabled', 'true', 'boolean', 'Enable automatic login'),
            ('headless_mode', 'false', 'boolean', 'Run browser in headless mode'),
            ('implicit_wait_time', '30', 'integer', 'Default wait time for elements'),
            ('page_load_timeout', '60', 'integer', 'Page load timeout in seconds'),
            ('max_login_attempts', '3', 'integer', 'Maximum login attempts'),
            ('screenshot_on_error', 'true', 'boolean', 'Take screenshot on errors'),
            ('performance_monitoring', 'true', 'boolean', 'Enable performance monitoring'),
            ('competitor_analysis', 'true', 'boolean', 'Enable competitor analysis'),
            ('marketplace_region', 'US', 'string', 'Default marketplace region'),
            ('price_optimization', 'true', 'boolean', 'Enable price optimization'),
            ('auto_messaging', 'false', 'boolean', 'Enable auto messaging'),
            ('data_backup_enabled', 'true', 'boolean', 'Enable automatic data backup')
        ]

        for key, value, value_type, description in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO bot_settings (setting_key, setting_value, setting_type, description)
                VALUES (?, ?, ?, ?)
            ''', (key, value, value_type, description))

    def get_setting(self, key, default=None):
        """Get setting value from database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT setting_value FROM bot_settings WHERE setting_key = ? AND is_active = 1', (key,))
            result = cursor.fetchone()
            return result[0] if result else default
        except Exception as e:
            self.logger.error(f"Error getting setting {key}: {e}")
            return default

    def update_setting(self, key, value):
        """Update setting value"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE bot_settings
                SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE setting_key = ?
            ''', (value, key))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error updating setting {key}: {e}")
            return False

    def log_operation(self, operation_data):
        """Log bot operation details"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bot_operations
                (operation_type, operation_subtype, status, items_processed, items_successful, items_failed,
                 error_message, stack_trace, browser_session_id, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                operation_data.get('operation_type'),
                operation_data.get('operation_subtype'),
                operation_data.get('status'),
                operation_data.get('items_processed', 0),
                operation_data.get('items_successful', 0),
                operation_data.get('items_failed', 0),
                operation_data.get('error_message'),
                operation_data.get('stack_trace'),
                operation_data.get('browser_session_id'),
                operation_data.get('ip_address'),
                operation_data.get('user_agent')
            ))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Error logging operation: {e}")
            return None

    def save_listing_to_db(self, listing_data):
        """Save listing to database"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO listings
                (item_id, url, title, price, location, status, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                listing_data['item_id'],
                listing_data['url'],
                listing_data['title'],
                listing_data.get('price', ''),
                listing_data.get('location', ''),
                listing_data.get('status', 'active'),
                listing_data.get('metadata', '{}')
            ))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error saving listing to DB: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

# ==============================================
# BROWSER MANAGEMENT CLASS
# ==============================================

class AdvancedBrowserManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = AdvancedLogger()
        self.driver = None
        self.wait = None
        self.actions = None
        self.current_session_id = None

    def initialize_browser(self):
        """Advanced browser initialization with multiple configurations"""
        try:
            chrome_options = webdriver.ChromeOptions()

            # Basic configuration
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Performance optimization
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")

            # Headless mode configuration
            if self.db_manager.get_setting('headless_mode') == 'true':
                chrome_options.add_argument("--headless=new")

            # User agent rotation
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")

            # Additional preferences
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 1,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            }
            chrome_options.add_experimental_option("prefs", prefs)

            # Initialize driver
            self.driver = webdriver.Chrome(options=chrome_options)

            # Additional anti-detection
            if self.driver:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
                self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")

            # Configure waits
            wait_time = int(self.db_manager.get_setting('implicit_wait_time', 30))
            if self.driver:
                self.wait = WebDriverWait(self.driver, wait_time)
                self.driver.implicitly_wait(wait_time)
                self.driver.set_page_load_timeout(int(self.db_manager.get_setting('page_load_timeout', 60)))

            # Initialize actions
            if self.driver:
                self.actions = ActionChains(self.driver)

            # Generate session ID
            self.current_session_id = hashlib.md5(str(datetime.datetime.now()).encode()).hexdigest()[:16]

            self.logger.info(f"✅ Advanced browser initialized successfully - Session: {self.current_session_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Browser initialization failed: {e}")
            return False

    def safe_find_element(self, locator_strategy, locator_value, timeout=None):
        """Safely find element with multiple fallback strategies"""
        if not self.driver:
            return None

        strategies = {
            'xpath': By.XPATH,
            'css': By.CSS_SELECTOR,
            'id': By.ID,
            'name': By.NAME,
            'class': By.CLASS_NAME,
            'tag': By.TAG_NAME,
            'link': By.LINK_TEXT,
            'partial_link': By.PARTIAL_LINK_TEXT
        }

        if timeout is None:
            timeout = int(self.db_manager.get_setting('implicit_wait_time', 30))

        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((strategies[locator_strategy], locator_value)))
            return element
        except Exception as e:
            self.logger.debug(f"Element not found with {locator_strategy}: {locator_value} - {e}")
            return None

    def safe_click(self, element, max_attempts=3):
        """Safely click element with multiple attempts"""
        if not self.driver or not element:
            return False

        for attempt in range(max_attempts):
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
                element.click()
                return True
            except Exception as e:
                self.logger.debug(f"Click attempt {attempt + 1} failed: {e}")
                time.sleep(1)
        return False

    def take_screenshot(self, filename_prefix="screenshot"):
        """Take screenshot and save with timestamp"""
        try:
            if self.db_manager.get_setting('screenshot_on_error') == 'true' and self.driver:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename_prefix}_{timestamp}.png"
                self.driver.save_screenshot(filename)
                self.logger.info(f"📸 Screenshot saved: {filename}")
                return filename
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
        return None

    def close_browser(self):
        """Close browser and cleanup"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.actions = None
                self.logger.info("✅ Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")

# ==============================================
# FACEBOOK AUTHENTICATION CLASS
# ==============================================

class FacebookAuthenticator:
    def __init__(self, browser_manager, db_manager):
        self.browser_manager = browser_manager
        self.db_manager = db_manager
        self.logger = AdvancedLogger()
        self.cookies_file = "facebook_cookies.pkl"

    def smart_login(self, email, password):
        """Advanced login with multiple strategies"""
        operation_id = self.db_manager.log_operation({
            'operation_type': 'authentication',
            'operation_subtype': 'login',
            'status': 'started'
        })

        try:
            # Strategy 1: Try cookies first
            if self.try_cookie_login():
                self.db_manager.log_operation({
                    'operation_type': 'authentication',
                    'operation_subtype': 'login',
                    'status': 'success',
                    'browser_session_id': self.browser_manager.current_session_id
                })
                return True

            # Strategy 2: Normal login
            max_attempts = int(self.db_manager.get_setting('max_login_attempts', 3))
            for attempt in range(max_attempts):
                self.logger.info(f"🔄 Login attempt {attempt + 1}/{max_attempts}")

                if self.perform_login(email, password):
                    self.save_cookies()
                    self.db_manager.log_operation({
                        'operation_type': 'authentication',
                        'operation_subtype': 'login',
                        'status': 'success',
                        'browser_session_id': self.browser_manager.current_session_id
                    })
                    return True

                time.sleep(5)

            # Strategy 3: Check for security challenges
            if self.handle_security_challenges():
                self.db_manager.log_operation({
                    'operation_type': 'authentication',
                    'operation_subtype': 'login',
                    'status': 'success',
                    'browser_session_id': self.browser_manager.current_session_id
                })
                return True

            self.db_manager.log_operation({
                'operation_type': 'authentication',
                'operation_subtype': 'login',
                'status': 'failed',
                'error_message': 'All login attempts failed'
            })
            return False

        except Exception as e:
            self.db_manager.log_operation({
                'operation_type': 'authentication',
                'operation_subtype': 'login',
                'status': 'error',
                'error_message': str(e),
                'stack_trace': str(sys.exc_info())
            })
            self.logger.error(f"❌ Login error: {e}")
            return False

    def try_cookie_login(self):
        """Try to login using saved cookies"""
        try:
            if os.path.exists(self.cookies_file) and self.browser_manager.driver:
                self.browser_manager.driver.get("https://facebook.com")
                time.sleep(2)

                with open(self.cookies_file, 'rb') as file:
                    cookies = pickle.load(file)

                for cookie in cookies:
                    self.browser_manager.driver.add_cookie(cookie)

                self.browser_manager.driver.refresh()
                time.sleep(5)

                # Verify login
                if self.is_logged_in():
                    self.logger.info("✅ Logged in via cookies")
                    return True

        except Exception as e:
            self.logger.debug(f"Cookie login failed: {e}")

        return False

    def perform_login(self, email, password):
        """Perform actual login with credentials"""
        try:
            if not self.browser_manager.driver:
                return False

            self.browser_manager.driver.get("https://facebook.com")
            time.sleep(5)

            # Fill email
            email_field = self.browser_manager.safe_find_element('name', 'email')
            if not email_field:
                self.logger.error("❌ Email field not found")
                return False

            email_field.clear()
            email_field.send_keys(email)
            time.sleep(1)

            # Fill password
            password_field = self.browser_manager.safe_find_element('name', 'pass')
            if not password_field:
                self.logger.error("❌ Password field not found")
                return False

            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)

            # Click login
            login_button = self.browser_manager.safe_find_element('name', 'login')
            if not login_button:
                self.logger.error("❌ Login button not found")
                return False

            self.browser_manager.safe_click(login_button)
            time.sleep(8)

            return self.is_logged_in()

        except Exception as e:
            self.logger.error(f"❌ Login perform error: {e}")
            return False

    def is_logged_in(self):
        """Check if user is logged in"""
        try:
            if not self.browser_manager.driver:
                return False

            # Check multiple indicators of successful login
            current_url = self.browser_manager.driver.current_url.lower()

            login_indicators = ['login', 'log in', 'signin', 'sign in']
            if any(indicator in current_url for indicator in login_indicators):
                return False

            # Check for home page elements
            home_indicators = [
                "//div[@role='navigation']",
                "//div[@data-pagelet='LeftRail']",
                "//span[text()='Home']",
                "//a[@aria-label='Home']"
            ]

            for indicator in home_indicators:
                element = self.browser_manager.safe_find_element('xpath', indicator, timeout=5)
                if element:
                    return True

            return False

        except Exception as e:
            self.logger.debug(f"Login check error: {e}")
            return False

    def handle_security_challenges(self):
        """Handle security challenges like 2FA, checkpoint, etc."""
        try:
            # Check for various security challenges
            security_checks = [
                self.handle_two_factor_auth,
                self.handle_checkpoint_challenge,
                self.handle_unusual_activity
            ]

            for check in security_checks:
                if check():
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Security challenge handling error: {e}")
            return False

    def handle_two_factor_auth(self):
        """Handle two-factor authentication"""
        # Implementation for 2FA would go here
        return False

    def handle_checkpoint_challenge(self):
        """Handle Facebook checkpoint challenges"""
        # Implementation for checkpoint handling would go here
        return False

    def handle_unusual_activity(self):
        """Handle unusual activity detection"""
        # Implementation for unusual activity handling would go here
        return False

    def save_cookies(self):
        """Save cookies for future sessions"""
        try:
            if self.browser_manager.driver:
                cookies = self.browser_manager.driver.get_cookies()
                with open(self.cookies_file, 'wb') as file:
                    pickle.dump(cookies, file)
                self.logger.info("✅ Cookies saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving cookies: {e}")

# ==============================================
# MARKETPLACE MANAGER CLASS
# ==============================================

class MarketplaceManager:
    def __init__(self, browser_manager, db_manager):
        self.browser_manager = browser_manager
        self.db_manager = db_manager
        self.logger = AdvancedLogger()

    def navigate_to_marketplace(self):
        """Navigate to Facebook Marketplace"""
        try:
            if not self.browser_manager.driver:
                return False

            self.browser_manager.driver.get("https://www.facebook.com/marketplace/you/selling")
            time.sleep(5)

            # Verify marketplace access
            if "marketplace" in self.browser_manager.driver.current_url:
                self.logger.info("✅ Successfully navigated to Marketplace")
                return True
            else:
                self.logger.error("❌ Failed to access Marketplace")
                return False

        except Exception as e:
            self.logger.error(f"❌ Marketplace navigation error: {e}")
            return False

    def get_active_listings(self):
        """Get all active listings from marketplace"""
        operation_id = self.db_manager.log_operation({
            'operation_type': 'marketplace',
            'operation_subtype': 'get_listings',
            'status': 'started'
        })

        try:
            if not self.navigate_to_marketplace():
                return []

            # Scroll to load all listings
            self.scroll_to_load_all_listings()

            # Find listing elements
            listing_elements = self.browser_manager.driver.find_elements(By.XPATH,
                "//a[contains(@href, '/marketplace/item/')]")

            listings_data = []
            for element in listing_elements:
                try:
                    listing_data = self.extract_listing_data(element)
                    if listing_data:
                        listings_data.append(listing_data)
                        self.db_manager.save_listing_to_db(listing_data)

                except Exception as e:
                    self.logger.debug(f"Error processing listing element: {e}")
                    continue

            self.db_manager.log_operation({
                'operation_type': 'marketplace',
                'operation_subtype': 'get_listings',
                'status': 'completed',
                'items_processed': len(listing_elements),
                'items_successful': len(listings_data),
                'items_failed': len(listing_elements) - len(listings_data)
            })

            self.logger.info(f"✅ Found {len(listings_data)} active listings")
            return listings_data

        except Exception as e:
            self.db_manager.log_operation({
                'operation_type': 'marketplace',
                'operation_subtype': 'get_listings',
                'status': 'error',
                'error_message': str(e),
                'stack_trace': str(sys.exc_info())
            })
            self.logger.error(f"❌ Error getting listings: {e}")
            return []

    def scroll_to_load_all_listings(self):
        """Scroll to load all marketplace listings"""
        try:
            if not self.browser_manager.driver:
                return

            last_height = self.browser_manager.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 10

            while scroll_attempts < max_scroll_attempts:
                # Scroll down
                self.browser_manager.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Calculate new scroll height
                new_height = self.browser_manager.driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    break

                last_height = new_height
                scroll_attempts += 1

        except Exception as e:
            self.logger.debug(f"Scroll error: {e}")

    def extract_listing_data(self, element):
        """Extract detailed listing data from element"""
        try:
            url = element.get_attribute('href')
            if not url or '/marketplace/item/' not in url:
                return None

            # Extract item ID from URL
            item_id = self.extract_item_id_from_url(url)

            # Extract title
            title = self.extract_listing_title(element)

            # Extract price
            price = self.extract_listing_price(element)

            # Extract location
            location = self.extract_listing_location(element)

            # Extract additional metadata
            metadata = {
                'url': url,
                'scraped_at': datetime.datetime.now().isoformat(),
                'element_text': element.text[:500] if element.text else ''
            }

            listing_data = {
                'item_id': item_id,
                'url': url,
                'title': title,
                'price': price,
                'location': location,
                'status': 'active',
                'metadata': json.dumps(metadata)
            }

            return listing_data

        except Exception as e:
            self.logger.debug(f"Error extracting listing data: {e}")
            return None

    def extract_item_id_from_url(self, url):
        """Extract item ID from listing URL"""
        try:
            # Multiple URL format patterns
            patterns = [
                r'/marketplace/item/(\d+)',
                r'fbid=(\d+)',
                r'item_id=(\d+)'
            ]

            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)

            # Fallback: hash the URL
            return hashlib.md5(url.encode()).hexdigest()[:16]

        except Exception as e:
            self.logger.debug(f"Error extracting item ID: {e}")
            return "unknown"

    def extract_listing_title(self, element):
        """Extract listing title"""
        try:
            # Multiple title extraction strategies
            title_selectors = [
                ".//span[@dir='auto']",
                ".//div[contains(@class, 'title')]",
                ".//h3",
                ".//div[@class='title']"
            ]

            for selector in title_selectors:
                try:
                    title_element = element.find_element(By.XPATH, selector)
                    if title_element and title_element.text.strip():
                        return title_element.text.strip()[:200]
                except:
                    continue

            return "Unknown Title"

        except Exception as e:
            self.logger.debug(f"Error extracting title: {e}")
            return "Unknown Title"

    def extract_listing_price(self, element):
        """Extract listing price"""
        try:
            # Multiple price extraction strategies
            price_selectors = [
                ".//span[contains(text(), '$')]",
                ".//div[contains(@class, 'price')]",
                ".//span[contains(@class, 'price')]"
            ]

            for selector in price_selectors:
                try:
                    price_element = element.find_element(By.XPATH, selector)
                    if price_element and price_element.text.strip():
                        price_text = price_element.text.strip()
                        # Extract price using regex
                        price_match = re.search(r'\$?(\d+[.,]?\d*)', price_text)
                        if price_match:
                            return price_match.group(0)
                except:
                    continue

            return ""

        except Exception as e:
            self.logger.debug(f"Error extracting price: {e}")
            return ""

    def extract_listing_location(self, element):
        """Extract listing location"""
        try:
            # Multiple location extraction strategies
            location_selectors = [
                ".//span[contains(@class, 'location')]",
                ".//div[contains(@class, 'location')]",
                ".//span[contains(text(), ', ')]"
            ]

            for selector in location_selectors:
                try:
                    location_element = element.find_element(By.XPATH, selector)
                    if location_element and location_element.text.strip():
                        return location_element.text.strip()[:100]
                except:
                    continue

            return ""

        except Exception as e:
            self.logger.debug(f"Error extracting location: {e}")
            return ""

    def refresh_listing(self, listing_url, item_id):
        """Refresh a single listing"""
        try:
            if not self.browser_manager.driver:
                return False

            self.logger.info(f"🔄 Refreshing listing: {item_id}")

            # Navigate to listing
            self.browser_manager.driver.get(listing_url)
            time.sleep(5)

            # Find and click edit button
            edit_button = self.browser_manager.safe_find_element('xpath', "//span[text()='Edit']")
            if not edit_button:
                edit_button = self.browser_manager.safe_find_element('xpath', "//button[contains(text(), 'Edit')]")

            if edit_button and self.browser_manager.safe_click(edit_button):
                time.sleep(3)

                # Find and click save button
                save_button = self.browser_manager.safe_find_element('xpath', "//span[text()='Save']")
                if not save_button:
                    save_button = self.browser_manager.safe_find_element('xpath', "//button[contains(text(), 'Save')]")

                if save_button and self.browser_manager.safe_click(save_button):
                    time.sleep(5)
                    self.logger.info(f"✅ Successfully refreshed listing: {item_id}")
                    return True

            self.logger.warning(f"⚠️ Could not refresh listing: {item_id}")
            return False

        except Exception as e:
            self.logger.error(f"❌ Error refreshing listing {item_id}: {e}")
            return False

    def refresh_all_listings(self, listings_data):
        """Refresh all listings"""
        operation_id = self.db_manager.log_operation({
            'operation_type': 'marketplace',
            'operation_subtype': 'refresh_listings',
            'status': 'started'
        })

        try:
            success_count = 0
            total_count = len(listings_data)

            for listing in listings_data:
                if self.refresh_listing(listing['url'], listing['item_id']):
                    success_count += 1
                    # Update listing in database
                    self.db_manager.save_listing_to_db({
                        'item_id': listing['item_id'],
                        'status': 'refreshed',
                        'last_refreshed': datetime.datetime.now().isoformat(),
                        'refresh_count': 1
                    })

                # Random delay between refreshes
                time.sleep(random.randint(2, 5))

            self.db_manager.log_operation({
                'operation_type': 'marketplace',
                'operation_subtype': 'refresh_listings',
                'status': 'completed',
                'items_processed': total_count,
                'items_successful': success_count,
                'items_failed': total_count - success_count
            })

            self.logger.info(f"✅ Refreshed {success_count}/{total_count} listings")
            return success_count, total_count

        except Exception as e:
            self.db_manager.log_operation({
                'operation_type': 'marketplace',
                'operation_subtype': 'refresh_listings',
                'status': 'error',
                'error_message': str(e),
                'stack_trace': str(sys.exc_info())
            })
            self.logger.error(f"❌ Error refreshing listings: {e}")
            return 0, 0

# ==============================================
# MAIN BOT CLASS
# ==============================================

class AdvancedFacebookBot:
    def __init__(self):
        self.logger = AdvancedLogger()
        self.db_manager = DatabaseManager()
        self.browser_manager = AdvancedBrowserManager(self.db_manager)
        self.auth_manager = FacebookAuthenticator(self.browser_manager, self.db_manager)
        self.marketplace_manager = MarketplaceManager(self.browser_manager, self.db_manager)
        self.is_running = False

    def initialize_bot(self):
        """Initialize all bot components"""
        try:
            self.logger.info("🚀 Initializing Advanced Facebook Bot...")

            # Initialize browser
            if not self.browser_manager.initialize_browser():
                return False

            self.logger.info("✅ Bot initialization completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Bot initialization failed: {e}")
            return False

    def run_single_cycle(self, email, password):
        """Run a single bot cycle"""
        try:
            self.logger.info("🔄 Starting bot cycle...")

            # Login
            if not self.auth_manager.smart_login(email, password):
                self.logger.error("❌ Login failed, stopping cycle")
                return False

            # Get active listings
            listings = self.marketplace_manager.get_active_listings()
            if not listings:
                self.logger.warning("⚠️ No listings found")
                return True

            # Refresh listings
            success_count, total_count = self.marketplace_manager.refresh_all_listings(listings)

            self.logger.info(f"🎉 Bot cycle completed: {success_count}/{total_count} listings refreshed")
            return True

        except Exception as e:
            self.logger.error(f"❌ Bot cycle error: {e}")
            return False

    def run_continuous(self, email, password, interval_hours=6):
        """Run bot continuously"""
        self.is_running = True
        cycle_count = 0

        self.logger.info(f"🔄 Starting continuous bot operation (interval: {interval_hours} hours)")

        while self.is_running:
            cycle_count += 1
            self.logger.info(f"🔄 Starting cycle {cycle_count}...")

            try:
                success = self.run_single_cycle(email, password)

                if success:
                    self.logger.info(f"✅ Cycle {cycle_count} completed successfully")
                else:
                    self.logger.error(f"❌ Cycle {cycle_count} failed")

                # Calculate next run time
                if self.is_running:
                    next_run = datetime.datetime.now() + datetime.timedelta(hours=interval_hours)
                    self.logger.info(f"⏰ Next cycle at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

                    # Wait for next cycle
                    wait_seconds = interval_hours * 3600
                    for remaining in range(wait_seconds, 0, -60):
                        if not self.is_running:
                            break
                        if remaining % 3600 == 0:
                            hours_remaining = remaining // 3600
                            self.logger.info(f"⏳ {hours_remaining} hours until next cycle...")
                        time.sleep(60)

            except Exception as e:
                self.logger.error(f"💥 Critical error in cycle {cycle_count}: {e}")
                time.sleep(300)  # Wait 5 minutes before retry

        self.logger.info("🛑 Continuous bot operation stopped")

    def stop(self):
        """Stop the bot"""
        self.is_running = False
        self.logger.info("🛑 Stopping bot...")
        self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.browser_manager.close_browser()
            self.db_manager.close()
            self.logger.info("✅ Bot cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

# ==============================================
# MAIN EXECUTION
# ==============================================

def main():
    """Main execution function"""
    bot = AdvancedFacebookBot()

    # Configuration
    EMAIL = "xofedi9676@rabitex.com"
    PASSWORD = "ASD@123"
    INTERVAL_HOURS = 6

    try:
        # Initialize bot
        if not bot.initialize_bot():
            sys.exit(1)

        # Run single cycle for testing
        bot.logger.info("🧪 Running single test cycle...")
        success = bot.run_single_cycle(EMAIL, PASSWORD)

        if success:
            bot.logger.info("🎉 Test cycle completed successfully!")

            # Ask user if they want to run continuously
            user_input = input("Do you want to run continuously? (y/n): ").lower().strip()
            if user_input in ['y', 'yes']:
                bot.logger.info("🔄 Starting continuous operation...")
                bot.run_continuous(EMAIL, PASSWORD, INTERVAL_HOURS)
            else:
                bot.logger.info("🛑 Single cycle completed, exiting...")
        else:
            bot.logger.error("💥 Test cycle failed!")

    except KeyboardInterrupt:
        bot.logger.info("🛑 Bot stopped by user")
    except Exception as e:
        bot.logger.error(f"💥 Fatal error: {e}")
    finally:
        bot.cleanup()

if __name__ == "__main__":
    main()
