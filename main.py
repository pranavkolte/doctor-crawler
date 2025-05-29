
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from db import init_db, save_doctor, get_all_doctors

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)




@dataclass
class Doctor:
    """Data class to store comprehensive doctor information"""
    name: str
    specialty: Optional[str] = None
    profile_url: Optional[str] = None
    image_url: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    has_multiple_locations: bool = False
    is_employed_provider: bool = False
    is_accepting_new_patients: bool = False
    rating: Optional[float] = 0
    rating_count: Optional[int] = 0
    

class AndalusiaHealthCrawler:
    """Web crawler for Andalusia Health website"""
    
    BASE_URL = "https://www.andalusiahealth.com"
    SEARCH_URL = f"{BASE_URL}/find-a-doctor/results?address=andalusia%2C+al&defaultSort=true"
    
    def __init__(self, headless: bool = True):
        """Initialize the crawler with configurable options"""
        self.headless = headless
        self.driver = None
    
    def setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with human-like settings"""
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        if self.headless:
            options.add_argument("--headless=new")
            
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def get_shadow_root(self, selector: str, timeout: int = 20):
        """Get shadow root element with proper waiting"""
        shadow_host = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return self.driver.execute_script("return arguments[0].shadowRoot", shadow_host)
    
    
    def extract_doctor_info(self, shadow_root) -> List[Doctor]:
        """Extract comprehensive doctor information from shadow DOM"""
        doctors = []
        
        # Find all doctor list item containers
        doctor_containers = shadow_root.find_elements(By.CSS_SELECTOR, "div.list-item-content")
        
        for container in doctor_containers:
            try:
                # Extract name
                name_element = container.find_element(By.CSS_SELECTOR, "span[itemprop='name'], a span.link_provider_display_name")
                name = name_element.text.strip() if name_element else "Unknown Doctor"
                
                # Extract URL if available
                url_element = container.find_element(By.CSS_SELECTOR, "a[href*='/provider']")
                url = url_element.get_attribute('href') if url_element else None
                if url and not url.startswith('http'):
                    url = self.BASE_URL + url
                
                # Extract specialty
                specialty_element = container.find_element(By.CSS_SELECTOR, "span[itemprop='medicalSpecialty']")
                specialty = specialty_element.text.strip() if specialty_element else None
                
                # Extract image URL
                image_url = None
                try:
                    img_element = container.find_element(By.CSS_SELECTOR, "div.provider-image img")
                    image_url = img_element.get_attribute('src')
                except:
                    pass
                
                # Extract location info
                # Extract location info
                location = None
                facility_name = None
                multiple_locations = False
                try:
                    # Check if doctor has multiple locations
                    try:
                        multiple_location_element = container.find_element(By.CSS_SELECTOR, "a[data-testref='provider-cards-location']")
                        if multiple_location_element and "+1 other location" in multiple_location_element.text:
                            multiple_locations = True
                    except:
                        pass
                    
                    # First try to get the facility/clinic name
                    facility_element = container.find_element(By.CSS_SELECTOR, "span[itemprop='name'][color='gray_800']")
                    facility_name = facility_element.text.strip() if facility_element else None
                    
                    # Then get the street address
                    address_element = container.find_element(By.CSS_SELECTOR, "span[itemprop='streetAddress']")
                    street_address = address_element.text.strip() if address_element else None
                    
                    # Combine facility name and address if both exist
                    if facility_name and street_address:
                        location = f"{facility_name}: {street_address}"
                    elif street_address:
                        location = street_address
                    elif facility_name:
                        location = facility_name
                except Exception as e:
                    logger.debug(f"Error extracting location: {str(e)}")
                    pass
                
                # Extract phone number
                phone = None
                try:
                    phone_element = container.find_element(By.CSS_SELECTOR, "a[href^='tel:']")
                    phone = phone_element.get_attribute('href').replace('tel:', '')
                except:
                    pass
                
                employed_provider = False
                accepts_new_patients = False
                try:
                    # Find badge elements that contain status information
                    badge_elements = container.find_elements(By.CSS_SELECTOR, "div.styles__Badge-sc-o9cga9-6 span")
                    for badge in badge_elements:
                        badge_text = badge.text.strip()
                        if "Employed Provider" in badge_text:
                            employed_provider = True
                        if "Accepts New Patients" in badge_text:
                            accepts_new_patients = True
                except Exception as e:
                    logger.debug(f"Error extracting provider status: {str(e)}")
                    pass
                
                employed_provider = False
                accepts_new_patients = False
                try:
                    # Find badge elements that contain status information
                    badge_elements = container.find_elements(By.CSS_SELECTOR, "div.styles__Badge-sc-o9cga9-6 span")
                    for badge in badge_elements:
                        badge_text = badge.text.strip()
                        if "Employed Provider" in badge_text:
                            employed_provider = True
                        if "Accepts New Patients" in badge_text:
                            accepts_new_patients = True
                except Exception as e:
                    logger.debug(f"Error extracting provider status: {str(e)}")
                    pass
                
                # Extract ratings if available
                rating = None
                rating_count = None
                try:
                    # Look for rating container
                    rating_element = container.find_element(By.CSS_SELECTOR, "div.loyal-stars[itemprop='aggregateRating']")
                    if rating_element:
                        # Extract rating value
                        rating_value_element = rating_element.find_element(By.CSS_SELECTOR, "span[itemprop='ratingValue']")
                        if rating_value_element:
                            rating_text = rating_value_element.text
                            # Extract just the numeric rating (e.g., "4.8" from "4.8 / 5")
                            rating = float(rating_text.split('/')[0].strip())
                        
                        # Extract rating count
                        rating_count_element = rating_element.find_element(By.CSS_SELECTOR, "span[itemprop='ratingCount']")
                        if rating_count_element:
                            count_text = rating_count_element.text.strip()
                            # Extract just the number from "(194)"
                            rating_count = int(count_text.strip('()'))
                except Exception as e:
                    # Rating information not available or couldn't be extracted
                    logger.debug(f"Error extracting ratings: {str(e)}")
                    pass
                
                # Create enhanced Doctor object
                doctor = Doctor(
                    name=name, 
                    specialty=specialty,
                    profile_url=url, 
                    image_url=image_url,
                    location=location,
                    phone=phone,
                    is_employed_provider=employed_provider,
                    is_accepting_new_patients=accepts_new_patients,
                    has_multiple_locations=multiple_locations,
                    rating=rating,
                    rating_count=rating_count
                )
                
                if name and name not in [d.name for d in doctors]:
                    doctors.append(doctor)
            except Exception as e:
                logger.error(f"Error extracting doctor info: {str(e)}")
                continue
            
        return doctors
    
    def crawl(self) -> List[Doctor]:
        """Main crawling method to retrieve doctor information"""
        self.driver = self.setup_driver()
        doctors = []
        
        try:
            logger.info("Loading search page...")
            self.driver.get(self.SEARCH_URL)
            
            # Wait for main content to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#loyal-search"))
            )
            
            # Get shadow root
            shadow_root = self.get_shadow_root("#loyal-search")
            
            # Wait for doctor cards to load within shadow DOM
            WebDriverWait(self.driver, 20).until(
                lambda d: shadow_root.find_elements(By.CSS_SELECTOR, "a[href*='provider']") or 
                          shadow_root.find_elements(By.CSS_SELECTOR, "span.text-md")
            )
            
            # Extract doctor information
            doctors = self.extract_doctor_info(shadow_root)
            
            if not doctors:
                logger.warning("No doctors found in the search results")
                
            return doctors
            
        except Exception as e:
            logger.error(f"Error during crawling: {str(e)}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main entry point for the crawler"""
    logger.info("Starting Andalusia Health doctor search...")
    session = init_db()
    session.close()
    crawler = AndalusiaHealthCrawler(headless=True)
    doctors = crawler.crawl()
    print(f"Found {len(doctors)} doctors:")
    
    for doctor in doctors:
        # Convert dataclass to dictionary for database storage
        doctor_dict = asdict(doctor)
        doctor_id = save_doctor(doctor_dict)
        logger.info(f"Saved doctor: {doctor.name} (ID: {doctor_id})")


if __name__ == "__main__":
    main()
