# ICON [[(6.59, 7.4), (9.39, 4.6), (1.99, -2.8), (1.99, -12.0), (-2.01, -12.0), (-2.01, -1.2), (6.59, 7.4)], [(-0.01, 18.0), (-2.77, 17.82), (-5.22, 17.33), (-6.81, 16.84), (-9.0, 15.88), (-10.82, 14.83), (-12.37, 13.73), (-13.38, 12.88), (-14.8, 11.47), (-16.53, 9.28), (-17.71, 7.33), (-18.44, 5.84), (-18.93, 4.56), (-19.44, 2.82), (-19.69, 1.62), (-19.93, -0.24), (-19.98, -3.03), (-19.82, -4.82), (-19.36, -7.14), (-18.78, -8.99), (-18.18, -10.41), (-16.87, -12.77), (-15.61, -14.52), (-14.53, -15.77), (-13.03, -17.19), (-11.75, -18.19), (-9.49, -19.6), (-7.63, -20.48), (-5.31, -21.29), (-2.8, -21.81), (-1.17, -21.97), (0.56, -22.0), (2.17, -21.89), (4.17, -21.57), (5.78, -21.15), (6.98, -20.74), (8.54, -20.07), (10.61, -18.95), (12.5, -17.62), (14.56, -15.73), (15.71, -14.38), (16.82, -12.81), (18.11, -10.45), (18.75, -8.94), (19.3, -7.26), (19.84, -4.56), (19.98, -2.76), (19.98, -1.18), (19.8, 0.82), (19.39, 2.89), (18.67, 5.12), (17.97, 6.73), (16.56, 9.2), (15.45, 10.7), (13.58, 12.69), (11.88, 14.09), (10.45, 15.06), (9.16, 15.79), (6.7, 16.87), (5.01, 17.38), (2.25, 17.88), (0.04, 18.0)], [(-0.01, -2.0)], [(-0.01, 14.0), (1.87, 13.9), (3.1, 13.72), (4.92, 13.27), (6.57, 12.65), (7.85, 12.0), (9.95, 10.56), (11.26, 9.38), (12.07, 8.51), (13.65, 6.4), (14.66, 4.51), (15.18, 3.17), (15.75, 0.9), (15.93, -0.48), (15.99, -2.41), (15.75, -4.87), (15.46, -6.25), (14.87, -8.01), (14.31, -9.23), (13.28, -10.95), (12.42, -12.08), (11.05, -13.55), (9.91, -14.56), (8.05, -15.86), (6.45, -16.69), (4.54, -17.39), (3.36, -17.68), (1.71, -17.92), (0.44, -18.0), (-1.44, -17.94), (-2.97, -17.75), (-5.29, -17.16), (-6.71, -16.59), (-8.07, -15.88), (-10.05, -14.49), (-11.32, -13.34), (-12.48, -12.07), (-13.2, -11.12), (-14.1, -9.69), (-14.72, -8.44), (-15.33, -6.79), (-15.77, -4.91), (-15.98, -3.05), (-16.0, -1.85), (-15.9, -0.04), (-15.44, 2.39), (-14.95, 3.89), (-14.24, 5.45), (-13.24, 7.08), (-12.22, 8.41), (-11.39, 9.31), (-10.07, 10.49), (-8.57, 11.58), (-7.27, 12.32), (-5.83, 12.96), (-4.11, 13.51), (-1.72, 13.91), (-0.06, 14.0)]]
# NAME Booking display
# DESC Is this table free?

# Replace the imports section with this:
import datetime
import utime
import json
import argparse
import os
import pickle

# Use urequests instead of requests for MicroPython
try:
    import urequests as requests
except ImportError:
    try:
        import requests
    except ImportError:
        print("Neither urequests nor requests module found")

# Import ntptime for time synchronization
try:
    import ntptime
except ImportError:
    print("ntptime module not found - time sync will be disabled")

# Function to check if file exists in MicroPython
def file_exists(filename):
    """Check if a file exists in MicroPython environment"""
    try:
        with open(filename, 'rb'):
            pass
        return True
    except OSError:  # MicroPython uses OSError for file not found
        return False

# Function to synchronize time via NTP
def sync_time_via_ntp(max_retries=3, retry_delay=5):
    """
    Synchronize the device's RTC with NTP time.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        retry_delay (int): Delay in seconds between retries
    
    Returns:
        bool: True if sync successful, False otherwise
    """
    if 'ntptime' not in globals():
        print("NTP sync skipped - ntptime module not available")
        return False
    
    for attempt in range(max_retries):
        try:
            print(f"Syncing time via NTP (attempt {attempt + 1}/{max_retries})...")
            ntptime.settime()
            
            # Get current time to verify sync worked
            current_time = utime.time()
            time_tuple = utime.gmtime(current_time)
            time_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} UTC".format(
                time_tuple[0], time_tuple[1], time_tuple[2],
                time_tuple[3], time_tuple[4], time_tuple[5]
            )
            
            print(f"Time synchronized successfully: {time_str}")
            return True
            
        except Exception as e:
            print(f"NTP sync attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                utime.sleep(retry_delay)
            else:
                print("All NTP sync attempts failed - continuing with system time")
    
    return False

# Try to import secrets first
try:
    import secrets
    print("Secrets file imported successfully")
except ImportError:
    print("Failed to import secrets.py. Please create this file with your credentials.")
    secrets = None

try:
    #this will be only here on presto 
    from presto import Presto

    # Setup for the Presto display
    presto = Presto()
    display = presto.display
    # Presto assumes you have a secrets.py with the format:
    #
    # WIFI_SSID = "Your SSID"
    # WIFI_PASSWORD = "Password"
    # MS_CLIENT_ID = "your-client-id"
    # MS_CLIENT_SECRET = "your-client-secret"
    # MS_TENANT_ID = "your-tenant-id"
    # ROOM_EMAIL = "room@example.com"
    connection_successful = presto.connect()
    
    # Sync time via NTP after successful WLAN connection
    if connection_successful:
        print("WLAN connected successfully, syncing time...")
        sync_time_via_ntp()
    else:
        print("WLAN connection failed - skipping NTP sync")
        
except ImportError:
    presto = None
    print("Failed to import Presto. Please ensure the module is installed.")
except Exception as e:
    print(f"An error occurred: {e}")

# TODO
# [x] SET LED COLOR
# [x] UPDaTE UI
# [ ] CANCEL BUTTON
# [x] loop call
# [x] handle full day events
# [x] Show time to next meeting
# [x] Orange LEDs when meeting is less than an hour away


# Cache duration in seconds (default: 1 minute)
# Override with CACHE_DURATION from secrets.py if available
DEFAULT_CACHE_DURATION = getattr(secrets, 'CACHE_DURATION', 60) if secrets else 60

# Define RGB color values as individual components
RED_R, RED_G, RED_B = 255, 0, 0
GREEN_R, GREEN_G, GREEN_B = 0, 255, 0  
WHITE_R, WHITE_G, WHITE_B = 255, 255, 255
ORANGE_R, ORANGE_G, ORANGE_B = 255, 165, 0  # Orange color for upcoming meetings



# Add this function to dynamically determine the current timezone offset
def get_berlin_utc_offset(timestamp=None):
    """
    Get Berlin's UTC offset in hours, accounting for DST.
    
    In Berlin (Central European Time):
    - Standard Time (winter): UTC+1
    - Summer Time (DST): UTC+2
    
    DST rules (as of 2024):
    - Starts: Last Sunday in March at 01:00 UTC (02:00 local time)
    - Ends: Last Sunday in October at 01:00 UTC (03:00 local time)
    
    Args:
        timestamp (int, optional): Unix timestamp to check. Defaults to current time.
    
    Returns:
        int: UTC offset in hours (1 for standard time, 2 for DST)
    """
    import utime
    
    # Use current time if no timestamp provided
    if timestamp is None:
        timestamp = utime.time()
    
    # Convert to time tuple
    time_tuple = utime.gmtime(timestamp)
    year = time_tuple[0]
    month = time_tuple[1]
    day = time_tuple[2]
    
    # Default to standard time (UTC+1)
    offset = 1
    
    # Basic check if we're in DST period (April through October)
    if month > 3 and month < 10:
        # Definitely in DST
        offset = 2
    elif month == 3:
        # March - check if we've passed the last Sunday
        
        # Calculate day of last Sunday in March
        # Get the weekday of March 31 (0=Monday, 6=Sunday)
        march_31 = calculate_weekday(year, 3, 31)
        # Calculate the date of the last Sunday
        last_sunday_date = 31 - ((march_31 + 1) % 7)
        
        # If today is after or on the last Sunday AND we're on/after 01:00 UTC
        if day > last_sunday_date or (day == last_sunday_date and time_tuple[3] >= 1):
            offset = 2
    elif month == 10:
        # October - check if we're before the last Sunday
        
        # Calculate day of last Sunday in October
        # Get the weekday of October 31
        october_31 = calculate_weekday(year, 10, 31)
        # Calculate the date of the last Sunday
        last_sunday_date = 31 - ((october_31 + 1) % 7)
        
        # If today is before the last Sunday OR it's the last Sunday but before 01:00 UTC
        if day < last_sunday_date or (day == last_sunday_date and time_tuple[3] < 1):
            offset = 2
    
    return offset

# Helper function to calculate weekday
def calculate_weekday(year, month, day):
    """Calculate weekday using Zeller's congruence algorithm"""
    if month < 3:
        month += 12
        year -= 1
    K = year % 100
    J = year // 100
    weekday = (day + ((13 * (month + 1)) // 5) + K + (K // 4) + (J // 4) - (2 * J)) % 7
    # Convert from Zeller's output (0=Saturday) to Python's (0=Monday, 6=Sunday)
    return (weekday + 5) % 7

def get_ms_graph_token(client_id, client_secret, tenant_id):
    """
    Get Microsoft Graph API token using client credentials flow (no user interaction).
    
    Args:
        client_id (str): Microsoft App client ID
        client_secret (str): Microsoft App client secret
        tenant_id (str): Azure AD tenant ID
    
    Returns:
        str: Access token
    """
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    # Create payload as URL-encoded form data string (not a dictionary)
    form_data = (
        f"grant_type=client_credentials&"
        f"client_id={client_id}&"
        f"client_secret={client_secret}&"
        f"scope=https://graph.microsoft.com/.default"
    )
    
    # Set correct content type for form data
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        print("Sending token request...")
        
        # Make the POST request with string form data, not dictionary
        response = requests.post(
            token_url, 
            data=form_data,  # Pre-formatted string, not a dictionary
            headers=headers
        )
        
        print(f"Token response status: {response.status_code}")
        
        # Check status code
        if response.status_code != 200:
            # Get error content as bytes and decode
            try:
                error_content = response.content
                error_text = error_content.decode('utf-8')
                print(f"Error response: {error_text[:100]}...")  # Print first 100 chars
            except Exception as decode_err:
                error_text = f"Failed to decode error response: {decode_err}"
                print(error_text)
            
            raise Exception(f"Token request failed: {error_text}")
        
        # Parse JSON response
        try:
            # Get response content as bytes first
            content = response.content
            print(f"Response content length: {len(content)} bytes")
            
            # Decode content to string
            content_str = content.decode('utf-8')
            
            # Parse JSON
            import json
            token_data = json.loads(content_str)
            
            print("Successfully parsed token response")
            
        except Exception as json_err:
            print(f"Error parsing token response: {json_err}")
            raise Exception(f"Failed to parse token response: {json_err}")
        
        # Always close the response to free resources
        response.close()
        
        return token_data.get('access_token')
    
    except Exception as e:
        print(f"Error in get_ms_graph_token: {e}")
        raise

# Add this new function to process calendar data
def process_calendar_data(email, calendar_data, current_time_seconds, current_time_str, start_time_str=None, end_time_str=None):
    """
    Process the calendar data (either cached or fresh) to determine room status.
    
    Args:
        email (str): Email address of the room resource
        calendar_data (dict): Raw calendar data from Microsoft Graph API
        current_time_seconds (int): Current time in seconds
        current_time_str (str): Current time as ISO string
        start_time_str (str, optional): Start time window as ISO string
        end_time_str (str, optional): End time window as ISO string
    
    Returns:
        dict: Processed room booking information
    """
    # Handle the case where calendar_data is None (network errors, etc.)
    if calendar_data is None:
        return {
            "room_email": email,
            "query_time": current_time_str,
            "timestamp": current_time_seconds,
            "error": "No calendar data available",
            "current_status": "Unknown"
        }
    
    # Get events from calendar data, with empty list as default
    events = calendar_data.get('value', [])
    print(f"Processing {len(events)} events")
    
    # Create result structure
    result = {
        "room_email": email,
        "query_time": current_time_str,
        "timestamp": current_time_seconds,
        "time_window": {
            "start": start_time_str,
            "end": end_time_str,
        },
        "current_status": "Available",
        "current_booking": None,
        "next_booking": None,
        "nearby_bookings": [],
        "time_until_next": None  # Add time until next meeting in minutes
    }
    
    # Process each calendar event and first identify if any is current
    current_booking_id = None
    all_bookings = []
    
    for event in events:
        booking = {
            "subject": event.get('subject', 'No Subject'),
            "organizer": event.get('organizer', {}).get('emailAddress', {}).get('address', 'Unknown'),
            "start": event.get('start', {}).get('dateTime', ''),
            "end": event.get('end', {}).get('dateTime', ''),
            "is_all_day": event.get('isAllDay', False),
            "location": event.get('location', {}).get('displayName', ''),
            "id": event.get('id', '')
        }
        
        try:
            if check_current_booking(booking, current_time_seconds):
                result["current_status"] = "Occupied"
                result["current_booking"] = booking
                current_booking_id = booking["id"]
            else:
                all_bookings.append(booking)
        except Exception as e:
            print(f"Error processing booking: {e}")
            # Still add to all_bookings even if there's an error in date parsing
            all_bookings.append(booking)
    
    # Add all non-current bookings to nearby_bookings
    result["nearby_bookings"] = all_bookings
    
    # Sort bookings by start time
    try:
        result["nearby_bookings"].sort(key=lambda x: parse_iso_date(x["start"]))
    except Exception as e:
        print(f"Error sorting bookings: {e}")
    
    # Find next booking if room is available
    if result["current_status"] == "Available":
        try:
            future_bookings = []
            for b in result["nearby_bookings"]:
                start_ts = parse_iso_date(b["start"])
                if start_ts > current_time_seconds:
                    future_bookings.append((start_ts, b))
                    
            # Sort by start time
            future_bookings.sort(key=lambda x: x[0])
            
            if future_bookings:
                result["next_booking"] = future_bookings[0][1]
                
                # Calculate time until next meeting in minutes
                time_until_next_seconds = future_bookings[0][0] - current_time_seconds
                result["time_until_next"] = int(time_until_next_seconds / 60)  # Convert to minutes
                
        except Exception as e:
            print(f"Error finding next booking: {e}")
    
    return result

def get_current_room_status(email, client_id, client_secret, tenant_id, output_file=None, cache_file=None, cache_duration=DEFAULT_CACHE_DURATION):
    """
    Retrieves the current booking status for a Microsoft 365 room resource with caching.
    Uses service-to-service authentication (no browser login required).
    
    Args:
        email (str): Email address of the room resource
        client_id (str): Microsoft App client ID
        client_secret (str): Microsoft App client secret
        tenant_id (str): Azure AD tenant ID
        output_file (str): Path to save JSON output (optional)
        cache_file (str): Path to the cache file (default: .room_cache.pkl)
        cache_duration (int): Cache duration in seconds (default: 300s / 5min)
    
    Returns:
        dict: Room booking information in JSON format
    """
    # Set default cache file if not provided
    if cache_file is None:
        cache_file = f".{email.split('@')[0]}_cache.pkl"

    # Initialize variables
    calendar_data = None
    current_time_seconds = utime.time()
    current_tuple = utime.gmtime(current_time_seconds)
    current_time_str = format_iso_time(current_tuple)
    
    # Check if cache exists and is valid using our file_exists function
    use_cached_data = False
    if file_exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Check if cache is still valid
            cache_age = current_time_seconds - cache_data['timestamp']
            if cache_age < cache_duration:
                print(f"Using cached data (age: {cache_age:.1f}s)")
                calendar_data = cache_data['calendar_data']
                use_cached_data = True
            else:
                print(f"Cache expired (age: {cache_age:.1f}s)")
        except Exception as e:
            print(f"Cache error: {e}")
    
    # If not using cached data, fetch fresh data from API
    if not use_cached_data:
        try:
            # Initialize events as an empty list
            events = []
            
            # Get Microsoft Graph API token
            access_token = get_ms_graph_token(client_id, client_secret, tenant_id)
            
            # Set up the headers for Graph API requests
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Calculate start and end times using utime
            # For MicroPython, avoid using fromtimestamp
            # Calculate time windows in seconds
            start_time_seconds = current_time_seconds - 1200*60  # 1200 minutes back
            end_time_seconds = current_time_seconds + 24*60*60   # 24 hours ahead
            
            # Format as ISO strings (simplified)
            # Use gmtime to get tuple of time components
            start_tuple = utime.gmtime(start_time_seconds)
            end_tuple = utime.gmtime(end_time_seconds)
            
            start_time_str = format_iso_time(start_tuple)
            end_time_str = format_iso_time(end_tuple)
        
            # Get room calendar events using Microsoft Graph API
            # Manually construct the URL with query parameters instead of using 'params'
            calendar_base_url = f"https://graph.microsoft.com/v1.0/users/{email}/calendar/calendarView"
            query_string = (
                f"?startDateTime={start_time_str}"
                f"&endDateTime={end_time_str}"
                f"&$select=subject,organizer,start,end,isAllDay,location,id"
            )
            calendar_url = calendar_base_url + query_string
            
            print(f"Calendar URL: {calendar_url[:100]}...")  # Print first 100 chars
            
            try:
                # Make GET request without 'params' parameter
                response = requests.get(calendar_url, headers=headers)
                
                print(f"Calendar response status: {response.status_code}")
                
                if response.status_code != 200:
                    # Get error content as bytes and decode
                    try:
                        error_content = response.content
                        error_text = error_content.decode('utf-8')
                        print(f"Error response: {error_text[:100]}...")  # Print first 100 chars
                    except Exception as decode_err:
                        error_text = f"Failed to decode error response: {decode_err}"
                        print(error_text)
                    
                    raise Exception(f"Calendar request failed: {error_text}")
                
                # Parse JSON response
                try:
                    # Get response content as bytes first
                    content = response.content
                    print(f"Response content length: {len(content)} bytes")
                    
                    # Decode content to string
                    content_str = content.decode('utf-8')
                    
                    # Parse JSON
                    import json
                    calendar_data = json.loads(content_str)
                    
                    print("Successfully parsed calendar response")
                    
                    # Cache only the raw calendar data and timestamp
                    cache_data = {
                        'timestamp': current_time_seconds,
                        'calendar_data': calendar_data
                    }
                    try:
                        with open(cache_file, 'wb') as f:
                            pickle.dump(cache_data, f)
                    except OSError as e:
                        print(f"Warning: Could not write cache file: {e}")
                    
                except Exception as json_err:
                    print(f"Error parsing calendar response: {json_err}")
                    raise
                
                # Always close the response
                response.close()
                
            except Exception as e:
                print(f"Request error: {e}")
                raise
                
        except Exception as e:
            print(f"Fetch error: {e}")
            calendar_data = None
    
    # Now process the data (cached or fresh)
    result = process_calendar_data(email, calendar_data, current_time_seconds, current_time_str, start_time_str if 'start_time_str' in locals() else None, end_time_str if 'end_time_str' in locals() else None)
    
    # Convert to JSON - Use dumps with error handling
    try:
        json_result = json.dumps(result)
    except Exception as e:
        print(f"Error converting to JSON: {e}")
        json_result = json.dumps({"error": "Failed to serialize result"})
    
    # Try to save to file if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write(json_result)
            print(f"Results saved to {output_file}")
        except OSError as e:
            print(f"Warning: Could not write output file: {e}")
    
    return result

# Main execution block with fixed color handling
# Improved time comparison code
def check_current_booking(booking, current_time_seconds):
    """
    Check if a booking is currently active.
    
    Args:
        booking (dict): Booking information with start and end times
        current_time_seconds (int): Current UTC timestamp in seconds
        
    Returns:
        bool: True if booking is current, False otherwise
    """
    try:
        # Get the start and end times as UTC timestamps
        booking_start_ts = parse_iso_date(booking.get("start", ""))
        booking_end_ts = parse_iso_date(booking.get("end", ""))
        
        # Check for all-day events - special handling
        if booking.get("is_all_day", False):
            # For all-day events, we need to check if current day falls within the event
            # We convert timestamps to dates and compare just the dates
            # This is a simplified approach
            current_date = utime.gmtime(current_time_seconds)[:3]  # (year, month, day)
            start_date = utime.gmtime(booking_start_ts)[:3]
            end_date = utime.gmtime(booking_end_ts)[:3]
            
            # Convert dates to comparable integers (YYYYMMDD format)
            current_int = current_date[0] * 10000 + current_date[1] * 100 + current_date[2]
            start_int = start_date[0] * 10000 + start_date[1] * 100 + start_date[2]
            end_int = end_date[0] * 10000 + end_date[1] * 100 + end_date[2]
            
            return start_int <= current_int <= end_int
        else:
            # Regular event - check if current time falls within start and end times
            return booking_start_ts <= current_time_seconds <= booking_end_ts
            
    except Exception as e:
        print(f"Error checking current booking: {e}")
        return False  # Assume not current on error
    
# Define function to format ISO time from tuple for reuse
def format_iso_time(time_tuple):
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(
        time_tuple[0], time_tuple[1], time_tuple[2],
        time_tuple[3], time_tuple[4], time_tuple[5]
    )

# Updated function to parse ISO 8601 dates with dynamic timezone adjustment
def parse_iso_date(iso_string):
    """
    Parse ISO 8601 date string from Microsoft Graph API and convert to UTC timestamp.
    
    Args:
        iso_string (str): ISO 8601 date string (e.g. "2025-04-25T14:30:00Z")
        
    Returns:
        int: Unix timestamp (seconds since epoch) in UTC
    """
    try:
        # Check if string is empty or None
        if not iso_string:
            return 0
            
        # Microsoft Graph API returns dates in UTC with 'Z' suffix
        # or with timezone offset like '+00:00'
        # Strip any timezone information and assume UTC
        if 'Z' in iso_string:
            iso_string = iso_string.replace('Z', '')
        elif '+' in iso_string:
            iso_string = iso_string.split('+')[0]
        elif '-' in iso_string and iso_string.count('-') > 2:  # More than date separators
            # Handle negative timezone offsets like '-01:00'
            parts = iso_string.split('-')
            iso_string = '-'.join(parts[:3])  # Keep just the date part and time
            if len(parts) > 3 and 'T' in parts[2]:
                # Handle time part
                time_parts = parts[2].split('T')
                if len(time_parts) == 2:
                    iso_string = f"{iso_string.split('T')[0]}T{time_parts[1]}"
        
        # Remove microseconds if present
        if '.' in iso_string:
            iso_string = iso_string.split('.')[0]
        
        # Should now be in format YYYY-MM-DDTHH:MM:SS
        try:
            date_part, time_part = iso_string.split('T')
        except ValueError:
            # If no T separator, assume date only with time 00:00:00
            date_part = iso_string
            time_part = "00:00:00"
            
        year, month, day = [int(x) for x in date_part.split('-')]
        
        # Handle potential missing seconds in time part
        time_components = time_part.split(':')
        hour = int(time_components[0])
        minute = int(time_components[1]) if len(time_components) > 1 else 0
        second = int(time_components[2]) if len(time_components) > 2 else 0
        
        # Get the current timezone offset including DST effect
        utc_offset = get_berlin_utc_offset()
        
        # Adjust the hours to compensate for timezone difference
        hour = hour + utc_offset
        
        # Handle hour underflow (might go negative)
        if hour < 0:
            hour += 24
            # Adjust the date backwards by one day
            timestamp = utime.mktime((year, month, day, 0, 0, 0, 0, 0)) - 86400  # Subtract one day
            # Then add the hours, minutes, seconds
            timestamp += hour * 3600 + minute * 60 + second
        # Handle hour overflow (24 or more)
        elif hour >= 24:
            hour -= 24
            # Adjust the date forward by one day
            timestamp = utime.mktime((year, month, day, 0, 0, 0, 0, 0)) + 86400  # Add one day
            # Then add the hours, minutes, seconds
            timestamp += hour * 3600 + minute * 60 + second
        else:
            # Normal case
            timestamp = utime.mktime((year, month, day, hour, minute, second, 0, 0))
            
        return timestamp
        
    except Exception as e:
        print(f"Error parsing date '{iso_string}': {e}")
        return 0  # Return epoch time as fallback

# Helper function to format time until next meeting
def format_time_until_next(minutes):
    """Format minutes into a human-readable string (e.g., '1h 30m')"""
    if minutes is None:
        return "No upcoming meetings"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours > 0:
        return f"{hours}h {remaining_minutes}m"
    else:
        return f"{remaining_minutes}m"

# Helper function to show an error message on the display
def show_message(message):
    """Display an error message on the Presto screen if available"""
    if presto:
        display.set_pen(BLACK)
        display.clear()
        display.set_pen(RED)
        
        # Split message into multiple lines if needed
        words = message.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) > 30:  # Rough character limit per line
                lines.append(current_line)
                current_line = word
            else:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
                    
        if current_line:
            lines.append(current_line)
            
        # Display each line
        y_pos = 10
        for line in lines:
            display.text(line, 10, y_pos, scale=1)
            y_pos += 20
            
        #presto.update()
    else:
        print(f"ERROR: {message}")
    
parser = argparse.ArgumentParser(description="Manage Microsoft 365 room bookings (no browser login)")
parser.add_argument("--action", choices=["status", "cancel"], default="status", 
                    help="Action to perform: check status or cancel booking")
parser.add_argument("--reason", help="Reason for cancellation (only used with --action cancel)")
parser.add_argument("--output", help="Path to save JSON output (only used with --action status)")
parser.add_argument("--cache-file", help="Path to the cache file (optional)")
parser.add_argument("--cache-duration", type=int, default=DEFAULT_CACHE_DURATION, 
                    help=f"Cache duration in seconds (default: {DEFAULT_CACHE_DURATION}s)")

args = parser.parse_args()

# Define pen colors for the display
BLACK = display.create_pen(0, 0, 0) if presto else None
RED = display.create_pen(255, 0, 0) if presto else None
WHITE = display.create_pen(255, 255, 255) if presto else None
GREEN = display.create_pen(0, 255, 0) if presto else None
ORANGE = display.create_pen(255, 165, 0) if presto else None  # Define orange pen

# Default values if secrets are not available
DEFAULT_EMAIL = "cloudlab@german-uds.de"
DEFAULT_CLIENT_ID = "1d25c5fc-03aa-4c7c-ba33-*****"
DEFAULT_CLIENT_SECRET = "nVi8Q~LuYo4VIAsrJy-*****"
DEFAULT_TENANT_ID = "72caeee7-aa36-4db8-a376-****"

# Get settings from secrets if available
room_email = getattr(secrets, 'ROOM_EMAIL', DEFAULT_EMAIL) if secrets else DEFAULT_EMAIL
client_id = getattr(secrets, 'MS_CLIENT_ID', DEFAULT_CLIENT_ID) if secrets else DEFAULT_CLIENT_ID
client_secret = getattr(secrets, 'MS_CLIENT_SECRET', DEFAULT_CLIENT_SECRET) if secrets else DEFAULT_CLIENT_SECRET
tenant_id = getattr(secrets, 'MS_TENANT_ID', DEFAULT_TENANT_ID) if secrets else DEFAULT_TENANT_ID

# Print the credentials being used (without exposing the full secret)
if client_secret and len(client_secret) > 8:
    masked_secret = client_secret[:4] + "..." + client_secret[-4:]
else:
    masked_secret = "[NOT SET]"

def show_easy_message(text):
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text(f"{text}", 5, 10, 200, 2)
    #presto.update()
    
show_easy_message("Connecting...")

print(f"Using room email: {room_email}")
print(f"Using client ID: {client_id}")
print(f"Using client secret: {masked_secret}")
print(f"Using tenant ID: {tenant_id}")

def handleresult(result):
    # Check if presto is not None and current_status is "Occupied" or "Available"
    if presto:
        display.set_font("bitmap8")
        
        if result["current_status"] == "Occupied":
            # Room is occupied - use red
            display.set_pen(RED)  
            display.clear()
            
            # Set all LEDs to red
            for i in range(7):
                presto.set_led_rgb(i, RED_R, RED_G, RED_B)
            
            # Set white pen for text
            display.set_pen(WHITE)
            
            # Handle missing current_booking
            if result.get("current_booking"):
                display.text(result["current_booking"].get("subject", "No Subject"), 10, 100, scale=2)
                display.text("booked by", 10, 200, scale=1)
                display.text(result["current_booking"].get("organizer", "Unknown"), 10, 220, scale=1)
                
                # Calculate remaining time for current meeting
                current_time_seconds = utime.time()
                booking_end_ts = parse_iso_date(result["current_booking"].get("end", ""))
                if booking_end_ts > current_time_seconds:
                    remaining_seconds = booking_end_ts - current_time_seconds
                    remaining_minutes = int(remaining_seconds / 60)
                    
                    # Display remaining time
                    display.text("Remaining time", 10, 145, scale=1)
                    display.text(format_time_until_next(remaining_minutes), 10, 165, scale=2)
            else:
                display.text("No booking details available", 10, 100, scale=1)
               
            # Update the display
            #presto.update()   
        elif result["current_status"] == "Available":
            time_until_next = result.get("time_until_next")
            
            if time_until_next is not None and time_until_next < 60:
                # Less than 1 hour until next meeting - use orange
                display.set_pen(ORANGE)
                display.clear()
                
                # Set all LEDs to orange
                for i in range(7):
                    presto.set_led_rgb(i, ORANGE_R, ORANGE_G, ORANGE_B)
                    
                display.set_pen(BLACK)
                display.set_font("Roboto-Medium")
                display.text("Available", 10, 10, scale=3)
                display.set_font("bitmap8")
                # Show upcoming meeting info
                display.text("Next meeting in:", 10, 60, scale=1)
                display.text(format_time_until_next(time_until_next), 10, 80, scale=2)
                
                if result.get("next_booking"):
                    display.text(result["next_booking"].get("subject", "No Subject"), 10, 120, scale=1)
                    display.text("by " + result["next_booking"].get("organizer", "Unknown"), 10, 140, scale=1)
                
                #presto.update()
            else:
                # More than 1 hour until next meeting or no upcoming meeting - use green
                display.set_pen(GREEN)
                display.clear()
                
                # Set all LEDs to green
                for i in range(7):
                    presto.set_led_rgb(i, GREEN_R, GREEN_G, GREEN_B)
                    
                display.set_pen(WHITE)
                display.set_font("Roboto-Medium")
                display.text("Available", 10, 10, scale=3)
                display.set_font("bitmap8")
                
                # Show upcoming meeting info if available
                if time_until_next is not None:
                    display.text("Next meeting in:", 10, 60, scale=1)
                    display.text(format_time_until_next(time_until_next), 10, 80, scale=2)
                    
                    if result.get("next_booking"):
                        display.text(result["next_booking"].get("subject", "No Subject"), 10, 120, scale=1)
                        display.text("by " + result["next_booking"].get("organizer", "Unknown"), 10, 140, scale=1)
                else:
                    display.text("No upcoming meetings", 10, 80, scale=1)
                
                display.text("Be sure to book this online, this is", 10, 198, scale=1)
                display.text(room_email, 10, 210, scale=1)
                display.text("so remote people are aware it is in use.", 10, 222, scale=1)
                
                #presto.updat()
        
        # Display the status for the occupied state
        # For the available state, we've already displayed it with specific coloring based on next meeting time
        if result["current_status"] == "Occupied":
            display.set_font("Roboto-Medium")
            display.text(result["current_status"], 10, 10, scale=3)
            display.set_font("bitmap8")
        
        # Update the display
        #presto.update()
        
    else:
        print("Presto is not available or the room status is not recognized.")
        # print(json.dumps(result, indent=2))
            
while True:
    try:
        result = get_current_room_status(
            email=room_email,
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
            output_file=args.output,
            cache_file=args.cache_file,
            cache_duration=args.cache_duration
        )
        
        handleresult(result)
        presto.update()
            
    except Exception as e:
        show_message(f"Error in main loop: {e}")
        
    # Wait before next iteration
    utime.sleep(60)

