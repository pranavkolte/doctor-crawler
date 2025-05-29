import logging
import json
from collections import defaultdict
from db import get_all_doctors

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def analyze_doctors():
    """
    Analyze doctor data to generate insights:
    1. Total number of doctors
    2. Total number of doctors with ratings
    3. Doctors having the same phone number
    4. Doctors with more than one location
    """
    # Get all doctors from the database
    doctors = get_all_doctors()
    
    # 1. Total number of doctors
    total_doctors = len(doctors)
    logger.info(f"Total number of doctors: {total_doctors}")
    
    # 2. Total number of doctors with ratings
    doctors_with_ratings = [doc for doc in doctors if doc.rating and doc.rating > 0]
    logger.info(f"Doctors with ratings: {len(doctors_with_ratings)} ({(len(doctors_with_ratings)/total_doctors*100):.1f}%)")
    
    # 3. Doctors having the same phone number
    phone_map = defaultdict(list)
    for doctor in doctors:
        if doctor.phone:
            phone_map[doctor.phone].append(doctor)
    
    doctors_with_shared_phones = {
        phone: docs for phone, docs in phone_map.items() if len(docs) > 1
    }
    
    logger.info(f"Found {len(doctors_with_shared_phones)} phone numbers shared by multiple doctors:")
    for phone, docs in doctors_with_shared_phones.items():
        logger.info(f"  Phone: {phone}")
        for doc in docs:
            logger.info(f"    - {doc.name} ({doc.specialty or 'No specialty listed'})")
    
    # 4. Doctors with more than one location
    doctors_multiple_locations = [doc for doc in doctors if doc.has_multiple_locations]
    logger.info(f"Doctors with multiple locations: {len(doctors_multiple_locations)} ({(len(doctors_multiple_locations)/total_doctors*100):.1f}%)")
    for doc in doctors_multiple_locations:
        logger.info(f"  - {doc.name} ({doc.specialty or 'No specialty listed'})")
    
    # Generate a summary report
    logger.info("SUMMARY REPORT:")
    logger.info(f"Total doctors: {total_doctors}")
    logger.info(f"Doctors with ratings: {len(doctors_with_ratings)}")
    logger.info(f"Number of shared phone numbers: {len(doctors_with_shared_phones)}")
    logger.info(f"Doctors with multiple locations: {len(doctors_multiple_locations)}")
    
    # Create report data structure for JSON
    report_data = {
        "summary": {
            "total_doctors": total_doctors,
            "doctors_with_ratings": len(doctors_with_ratings),
            "shared_phone_numbers": len(doctors_with_shared_phones),
            "doctors_with_multiple_locations": len(doctors_multiple_locations)
        },
        "shared_phone_numbers": {},
        "doctors_with_multiple_locations": []
    }
    
    # Add details for shared phone numbers
    for phone, docs in doctors_with_shared_phones.items():
        report_data["shared_phone_numbers"][phone] = [
            {
                "name": doc.name,
                "profile_url": doc.profile_url,
            } for doc in docs
        ]
    
    # Add details for doctors with multiple locations
    for doc in doctors_multiple_locations:
        report_data["doctors_with_multiple_locations"].append({
            "name": doc.name,
            "profile_url": doc.profile_url,
        })
    
    # Export as JSON
    with open("doctor_analysis_report.json", "w") as json_file:
        json.dump(report_data, json_file, indent=2)
    logger.info("Analysis report exported as doctor_analysis_report.json")
    
    return report_data

if __name__ == "__main__":
    analyze_doctors()