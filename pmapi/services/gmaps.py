import googlemaps
from pmapi.config import BaseConfig

def get_best_location_result(location):
    """
    Looks up a location string using the Google Maps API and returns the best result.
    
    Args:
        location (str): The location string to search for.
    
    Returns:
        dict: The best result containing location details (e.g., formatted address, coordinates).
              Returns None if no results are found.
    """
    # Initialize the Google Maps client
    gmaps = googlemaps.Client(key=BaseConfig.GMAPS_API_KEY)
    
    # Perform a geocode lookup
    try:
        results = gmaps.geocode(location)
        # Check if results are returned
        if results:
            # Get the best match (first result)
            best_result = results[0]
            place_id = best_result['place_id']
            
            # Use the place_id to get more detailed information about the place
            place_details = gmaps.place(place_id)
            
            result = None
            # Return the detailed information if available
            if 'result' in place_details:
                result = place_details['result']
                result['place_id'] = place_id
                result['description'] = get_full_address_from_place(result)

            return result  
        
        return None  # No results found from geocoding
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def get_full_address_from_place(place):
    """
    Extracts the full address from a Google Places API result object.
    
    Args:
        result (dict): A dictionary containing place information from Google Places API result
    
    Returns:
        str: A formatted full address string
    """
    # Check if the input data is valid
    if not place:
        return "No address available"
    
    # Try to use formatted_address if available
    if 'formatted_address' in place:
        return place['formatted_address']
    
    # If formatted_address is not available, construct address from components
    components = []
    
    # Add name if available
    if 'name' in place:
        components.append(place['name'])
    
    # Add street address components
    address_components = place.get('address_components', [])
    for component in address_components:
        # Add different levels of administrative areas
        if 'locality' in component['types'] or 'administrative_area_level_2' in component['types']:
            components.append(component['long_name'])
        elif 'administrative_area_level_1' in component['types']:
            components.append(component['long_name'])
    
    # Add country
    country = next((comp['long_name'] for comp in address_components if 'country' in comp['types']), '')
    if country:
        components.append(country)
    
    # Add postal code
    postal_code = next((comp['long_name'] for comp in address_components if 'postal_code' in comp['types']), '')
    if postal_code:
        components.append(postal_code)
    
    return ', '.join(components)