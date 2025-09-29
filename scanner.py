from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import sqlite3
import datetime
import random
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fixed_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class FixedFacebookBot:
    def __init__(self):
        self.driver = None
        self.wait = None

    def initialize_driver(self):
        """Simple driver setup"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--start-maximized")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            self.driver = webdriver.Chrome(options=options)
            if self.driver:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.wait = WebDriverWait(self.driver, 20)

            logging.info("✅ Driver initialized successfully")
            return True
        except Exception as e:
            logging.error(f" Driver initialization : {e}")
            return False

    def simple_login(self, email: str, password: str) -> bool:
        """Simple login system"""
        try:
            logging.info("🔐 Logging into Facebook...")

            if not self.driver:
                logging.error("❌ Driver not initialized")
                return False

            self.driver.get("https://www.facebook.com")
            time.sleep(5)

            # Check if already logged in
            if self.is_logged_in():
                logging.info("✅ Already logged in")
                return True

            # Simple element finding
            try:
                # Email field
                email_input = self.driver.find_element(By.NAME, "email")
                email_input.clear()
                email_input.send_keys(email)
                time.sleep(2)

                # Password field
                password_input = self.driver.find_element(By.NAME, "pass")
                password_input.clear()
                password_input.send_keys(password)
                time.sleep(2)

                # Login button
                login_button = self.driver.find_element(By.NAME, "login")
                login_button.click()
                time.sleep(8)

            except Exception as e:
                logging.error(f"Login elements not found: {e}")
                return False

            # Verify login
            if self.is_logged_in():
                logging.info("🎉 Login successful!")
                return True
            else:
                logging.error("❌ Login failed")
                return False

        except Exception as e:
            logging.error(f"❌ Login error: {e}")
            return False

    def is_logged_in(self):
        """Check if user is logged in"""
        try:
            if not self.driver:
                return False

            current_url = self.driver.current_url.lower()
            if any(x in current_url for x in ['facebook.com/home', 'facebook.com/?']):
                return True

            # Check for homepage elements
            try:
                if self.driver.find_element(By.XPATH, "//div[@aria-label='Facebook']"):
                    return True
            except:
                pass

            return False
        except:
            return False

    def go_to_marketplace(self):
        """Go to marketplace listings"""
        try:
            logging.info("🛍️ Navigating to marketplace...")

            if not self.driver:
                logging.error("❌ Driver not initialized")
                return False

            self.driver.get("https://www.facebook.com/marketplace/you/selling")
            time.sleep(8)

            # Verify we're on marketplace
            if "marketplace" in self.driver.current_url.lower():
                logging.info("✅ Successfully reached marketplace")
                return True
            else:
                logging.error("❌ Failed to reach marketplace")
                return False

        except Exception as e:
            logging.error(f"❌ Marketplace navigation error: {e}")
            return False

    def get_real_listings(self):
        """Get real marketplace listings"""
        try:
            logging.info("🔍 Looking for listings...")

            if not self.driver:
                logging.error("❌ Driver not initialized")
                return []

            # Scroll to load more listings
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # Find listing elements
            listings = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/marketplace/item/')]")

            # Filter real listings
            real_listings = []
            for listing in listings:
                try:
                    url = listing.get_attribute('href')
                    text = listing.text.strip()

                    # Only include listings with actual text (not empty or system elements)
                    if url and text and len(text) > 5:
                        real_listings.append({
                            'element': listing,
                            'url': url,
                            'text': text
                        })
                except:
                    continue

            logging.info(f"📊 Found {len(real_listings)} real listings")

            # Show first few listings
            for i, listing in enumerate(real_listings[:3]):
                logging.info(f"   {i+1}. {listing['text'][:40]}...")

            return real_listings

        except Exception as e:
            logging.error(f"❌ Error getting listings: {e}")
            return []

    def make_listing_public(self, listing):
        """Make listing public"""
        try:
            if not self.driver:
                logging.error("❌ Driver not initialized")
                return False

            listing_url = listing['url']
            listing_text = listing['text'][:30] + "..." if listing['text'] else "Unknown"

            logging.info(f"🔄 Processing: {listing_text}")

            # Open listing in new tab
            original_window = self.driver.current_window_handle
            self.driver.execute_script("window.open(arguments[0]);", listing_url)
            time.sleep(5)

            # Switch to new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(5)

            # Try to find edit button
            edit_found = False
            edit_selectors = [
                "//span[contains(text(), 'Edit')]",
                "//button[contains(text(), 'Edit')]",
                "//div[contains(text(), 'Edit')]"
            ]

            for selector in edit_selectors:
                try:
                    edit_btn = self.driver.find_element(By.XPATH, selector)
                    if edit_btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", edit_btn)
                        edit_found = True
                        logging.info("✅ Edit button clicked")
                        time.sleep(5)
                        break
                except:
                    continue

            if edit_found:
                # Try to save changes
                save_found = False
                save_selectors = [
                    "//span[contains(text(), 'Save')]",
                    "//button[contains(text(), 'Save')]",
                    "//div[contains(text(), 'Save')]"
                ]

                for selector in save_selectors:
                    try:
                        save_btn = self.driver.find_element(By.XPATH, selector)
                        if save_btn.is_displayed():
                            self.driver.execute_script("arguments[0].click();", save_btn)
                            save_found = True
                            logging.info("✅ Save button clicked")
                            time.sleep(5)
                            break
                    except:
                        continue

                if save_found:
                    logging.info("✅ Listing processed successfully")
                    result = True
                else:
                    logging.warning("⚠️ Could not save changes")
                    result = False
            else:
                logging.warning("⚠️ Edit button not found")
                result = False

            # Close tab and switch back
            self.driver.close()
            self.driver.switch_to.window(original_window)
            time.sleep(3)

            return result

        except Exception as e:
            logging.error(f"❌ Error processing listing: {e}")
            try:
                # Cleanup - close extra tabs
                if self.driver and len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    self.driver.close()
                if self.driver and self.driver.window_handles:
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return False

    def run_bot(self, email, password):
        """Main bot execution"""
        logging.info("🚀 Starting Facebook Bot")

        if not self.initialize_driver():
            return

        try:
            # Login
            if not self.simple_login(email, password):
                logging.error("❌ Bot stopped - login failed")
                return

            # Go to marketplace
            if not self.go_to_marketplace():
                logging.error("❌ Bot stopped - marketplace failed")
                return

            # Get listings
            listings = self.get_real_listings()

            if not listings:
                logging.info("ℹ️ No listings found")
                print("\n📝 No active listings found")
                return

            print(f"\n🎯 Found {len(listings)} listings to process")

            # Process listings
            success_count = 0

            for i, listing in enumerate(listings):
                print(f"\n🔄 Processing {i+1}/{len(listings)}: {listing['text'][:35]}...")

                if self.make_listing_public(listing):
                    success_count += 1
                    print("✅ SUCCESS - Listing processed")
                else:
                    print("❌ FAILED - Could not process")

                # Wait between listings
                if i < len(listings) - 1:
                    wait_time = random.randint(3, 6)
                    print(f"⏳ Waiting {wait_time} seconds...")
                    time.sleep(wait_time)

            # Final report
            print(f"\n{'='*50}")
            print("🎯 BOT COMPLETED")
            print(f"{'='*50}")
            print(f"📊 Total Listings: {len(listings)}")
            print(f"✅ Successfully Processed: {success_count}")
            print(f"❌ Failed: {len(listings) - success_count}")
            print(f"📈 Success Rate: {(success_count/len(listings))*100:.1f}%")
            print(f"{'='*50}")

            if success_count > 0:
                print("🎉 Check your Facebook Marketplace listings!")
            else:
                print("💡 No listings were processed successfully")

            logging.info(f"🎯 Bot completed: {success_count}/{len(listings)} successful")

        except Exception as e:
            logging.error(f"❌ Bot error: {e}")
            print(f"\n❌ ERROR: {e}")
        finally:
            self.close_driver()

    def close_driver(self):
        """Close driver"""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("✅ Driver closed")
            except:
                pass

# Main execution
if __name__ == "__main__":
    print("🚀 FACEBOOK MARKETPLACE BOT")
    print("✅ Fixed Version - Simple & Working")
    print("=" * 50)

    # Your credentials
    EMAIL = "xofedi9676@rabitex.com"
    PASSWORD = "ASD@123"

    # Create and run bot
    bot = FixedFacebookBot()
    bot.run_bot(EMAIL, PASSWORD)

    print(f"\n🕒 Bot finished at {datetime.datetime.now().strftime('%H:%M:%S')}")
