import json
import os
import requests
import base64
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Version marker to force new deployment - v1.1.0
# Get Telegram token from environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8150544076:AAF8GTQ-3CrkOdBvnOmJ85s0hKu0RE4swwE")

# Supabase connection details - Using environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "https://foliyzwhhkkfbemiptvp.supabase.co"))
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZvbGl5endoaGtrZmJlbWlwdHZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIwNDg1MDksImV4cCI6MjA1NzYyNDUwOX0.SgTPp2Vwzl1wDixlItMt9v7YLwyH7AbZwH8mPB-BkQw"))
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# Try to use service key if available, otherwise fall back to anon key
if SUPABASE_SERVICE_KEY:
    print("Using service role key for Supabase API")
    API_KEY = SUPABASE_SERVICE_KEY
else:
    print("Using anonymous key for Supabase API")
    API_KEY = SUPABASE_ANON_KEY

# REST API endpoints
REST_URL = f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else ""
HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
    "X-Client-Info": "python-telegram-bot-supabase-rest"
}

def test_supabase_connection():
    """Test connection to Supabase and database tables"""
    try:
        # Test basic connection
        response = requests.get(
            f"{REST_URL}/users",
            headers=HEADERS,
            params={"limit": 1}
        )
        
        if response.status_code in (200, 201, 204):
            print(f"Successfully connected to Supabase REST API (status: {response.status_code})")
            return True
        else:
            print(f"Failed to connect to Supabase REST API: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        return False

def save_user_to_supabase(user_data):
    """Save user data to Supabase"""
    try:
        # Check if user already exists
        check_response = requests.get(
            f"{REST_URL}/users",
            headers=HEADERS,
            params={"user_id": f"eq.{user_data['user_id']}"}
        )
        
        if check_response.status_code == 200 and check_response.json():
            # User exists, update
            print(f"Updating existing user {user_data['user_id']}")
            response = requests.patch(
                f"{REST_URL}/users",
                headers=HEADERS,
                params={"user_id": f"eq.{user_data['user_id']}"},
                json=user_data
            )
        else:
            # User doesn't exist, create
            print(f"Creating new user {user_data['user_id']}")
            response = requests.post(
                f"{REST_URL}/users",
                headers=HEADERS,
                json=user_data
            )
        
        if response.status_code in (200, 201, 204):
            print(f"Successfully saved user data for {user_data['user_id']}")
            return True
        else:
            print(f"Failed to save user data: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error saving user data: {str(e)}")
        return False

def save_message_to_supabase(message_data):
    """Save message to Supabase"""
    try:
        response = requests.post(
            f"{REST_URL}/message_history",
            headers=HEADERS,
            json=message_data
        )
        
        if response.status_code in (200, 201, 204):
            print(f"Successfully saved message for user {message_data['user_id']}")
            return True
        else:
            print(f"Failed to save message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error saving message: {str(e)}")
        return False

def save_media_to_supabase(media_data, file_content=None):
    """Save media data and file content to Supabase"""
    try:
        # Create a copy of the data to avoid modifying the original
        save_data = media_data.copy()
        
        # Add timestamp if not already present
        if 'timestamp' not in save_data:
            save_data['timestamp'] = datetime.now().isoformat()
            
        # If we have file content, save to storage
        storage_url = None
        if file_content:
            storage_url = upload_file_to_storage(file_content, save_data)
            if storage_url:
                save_data['storage_url'] = storage_url
                save_data['has_media'] = True
                print(f"File uploaded to storage: {storage_url}")
        
        # Save message metadata to database
        if save_message_to_supabase(save_data):
            print(f"Successfully saved media message for user {save_data['user_id']}")
            return True, storage_url
        else:
            print(f"Failed to save media message to database")
            return False, storage_url
    except Exception as e:
        print(f"Error saving media: {str(e)}")
        return False, None

def ensure_bucket_exists(bucket_name="telegram_media"):
    """Ensure that a storage bucket exists"""
    try:
        # Check if bucket exists
        response = requests.post(
            f"{SUPABASE_URL}/storage/v1/bucket",
            headers=HEADERS,
            json={"id": bucket_name, "name": bucket_name, "public": True}
        )
        
        # 409 means bucket already exists, which is fine
        if response.status_code in [200, 201, 409]:
            print(f"Bucket {bucket_name} exists or was created")
            
            # Make sure bucket is public regardless of whether it exists
            if response.status_code == 409:
                update_response = requests.put(
                    f"{SUPABASE_URL}/storage/v1/bucket/{bucket_name}",
                    headers=HEADERS,
                    json={"public": True}
                )
                print(f"Updated bucket visibility: {update_response.status_code}")
            
            return True
        else:
            print(f"Failed to create bucket: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error creating bucket: {str(e)}")
        return False

def upload_file_to_storage(file_content, metadata, bucket_name="telegram_media"):
    """Upload file to Supabase storage and return the URL"""
    try:
        # Make sure bucket exists
        if not ensure_bucket_exists(bucket_name):
            return None
            
        # Generate a unique filename
        user_id = metadata.get('user_id', 'unknown')
        message_id = metadata.get('message_id', int(time.time()))
        file_type = metadata.get('file_type', 'file')
        original_filename = metadata.get('file_name', '')
        
        # Generate a safe filename with extension if available
        extension = ""
        if original_filename and '.' in original_filename:
            extension = f".{original_filename.split('.')[-1]}"
            
        filename = f"user_{user_id}_{message_id}_{int(time.time())}{extension}"
        
        # Upload headers need to be different than JSON headers
        upload_headers = {
            "apikey": API_KEY,
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/octet-stream",
            "Cache-Control": "3600"
        }
        
        # Upload the file
        upload_response = requests.post(
            f"{SUPABASE_URL}/storage/v1/object/{bucket_name}/{filename}",
            headers=upload_headers,
            data=file_content
        )
        
        print(f"Upload response: {upload_response.status_code}")
        
        if upload_response.status_code in [200, 201]:
            # Get the proper public URL of the uploaded file
            supabase_project_ref = SUPABASE_URL.split("//")[1].split(".")[0]
            file_url = f"https://{supabase_project_ref}.supabase.co/storage/v1/object/public/{bucket_name}/{filename}"
            print(f"File uploaded: {file_url}")
            return file_url
        else:
            print(f"Upload failed: {upload_response.text}")
            
            # Try alternative endpoint
            if upload_response.status_code in [404, 400, 401, 403]:
                print("Trying alternative upload endpoint...")
                alt_upload_response = requests.post(
                    f"{SUPABASE_URL}/storage/v1/object/upload/{bucket_name}/{filename}",
                    headers=upload_headers,
                    data=file_content
                )
                
                print(f"Alternative upload response: {alt_upload_response.status_code}")
                
                if alt_upload_response.status_code in [200, 201]:
                    supabase_project_ref = SUPABASE_URL.split("//")[1].split(".")[0]
                    file_url = f"https://{supabase_project_ref}.supabase.co/storage/v1/object/public/{bucket_name}/{filename}"
                    print(f"File uploaded via alternative endpoint: {file_url}")
                    return file_url
            
            return None
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return None

def get_file_direct(file_id):
    """Get file info from Telegram API directly"""
    try:
        if not TELEGRAM_TOKEN:
            print("No token available for getting file info")
            return None
            
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile"
        params = {'file_id': file_id}
        response = requests.post(url, json=params)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                file_info = result.get('result', {})
                print(f"Got file info: {file_info}")
                return file_info
        
        print(f"Failed to get file info: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"Error getting file info: {str(e)}")
        return None

def download_file_direct(file_path):
    """Download file from Telegram API directly"""
    try:
        if not TELEGRAM_TOKEN:
            print("No token available for file download")
            return None
            
        url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        response = requests.get(url)
        
        if response.status_code == 200:
            print(f"File downloaded successfully, size: {len(response.content)} bytes")
            return response.content
        else:
            print(f"File download failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return None

def send_message(chat_id, text, parse_mode=None):
    """Send message to user"""
    try:
        if not TELEGRAM_TOKEN:
            print("No token available for sending message")
            return False
            
        params = {
            'chat_id': chat_id,
            'text': text
        }
        
        if parse_mode:
            params['parse_mode'] = parse_mode
            
        send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        response = requests.post(send_url, json=params)
        
        if response.status_code == 200:
            print(f"Message sent to {chat_id}")
            return True
        else:
            print(f"Failed to send message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return False

def get_diagnostic_report(user_id):
    """Generate a diagnostic report for debugging"""
    report = []
    report.append("📊 Diagnostic Report 📊")
    report.append(f"Time: {datetime.now().isoformat()}")
    report.append(f"User ID: {user_id}")
    
    # Check Supabase connection
    report.append("\n🔌 Supabase Connection:")
    connection_ok = test_supabase_connection()
    report.append(f"Connected: {'✅ Yes' if connection_ok else '❌ No'}")
    report.append(f"URL: {SUPABASE_URL}")
    
    # Get message count for user
    try:
        user_messages = requests.get(
            f"{REST_URL}/message_history",
            headers=HEADERS,
            params={"user_id": f"eq.{user_id}", "select": "count"}
        )
        
        if user_messages.status_code == 200:
            try:
                count = user_messages.json()[0]["count"]
            except (KeyError, IndexError):
                count = len(user_messages.json())
            report.append(f"\n📝 User Messages: {count}")
        else:
            report.append(f"\n📝 User Messages: Error fetching ({user_messages.status_code})")
    except Exception as e:
        report.append(f"\n📝 User Messages: Error ({str(e)})")
    
    # Check environment variables
    report.append("\n🔧 Environment:")
    report.append(f"TELEGRAM_TOKEN: {'Set' if TELEGRAM_TOKEN else 'Not set'}")
    report.append(f"SUPABASE_URL: {'Set' if SUPABASE_URL else 'Not set'}")
    report.append(f"SUPABASE_ANON_KEY: {'Set' if SUPABASE_ANON_KEY else 'Not set'}")
    report.append(f"SUPABASE_SERVICE_KEY: {'Set' if SUPABASE_SERVICE_KEY else 'Not set'}")
    
    print("Diagnostic report generated successfully")
    return "\n".join(report)

def handle_photo(update):
    """Handle photo messages"""
    try:
        chat_id = update["message"]["chat"]["id"]
        user = update["message"]["from"]
        user_id = user.get("id")
        message_id = update["message"].get("message_id")
        
        # Get the largest photo (last in array)
        photo_array = update["message"].get("photo", [])
        if not photo_array:
            print("No photo array found")
            return False
            
        largest_photo = photo_array[-1]
        file_id = largest_photo.get("file_id")
        if not file_id:
            print("No file_id found in photo")
            return False
            
        print(f"Processing photo with file_id: {file_id}")
        
        # Get file info
        file_info = get_file_direct(file_id)
        if not file_info or "file_path" not in file_info:
            print("Could not get file path information")
            send_message(chat_id, "📸 Your photo was received, but I couldn't process it.")
            return False
            
        # Download the file
        file_path = file_info["file_path"]
        file_content = download_file_direct(file_path)
        
        if not file_content:
            print("Failed to download photo file")
            send_message(chat_id, "📸 Your photo was received, but downloading failed.")
            return False
            
        # Save to database
        media_data = {
            "user_id": user_id,
            "message_id": message_id,
            "message_text": "📸 Photo",
            "file_type": "photo",
            "file_id": file_id,
            "timestamp": datetime.now().isoformat(),
            "caption": update["message"].get("caption", ""),
            "has_media": True
        }
        
        success, storage_url = save_media_to_supabase(media_data, file_content)
        
        # Send response
        if success:
            message = "📸 Your photo was received and stored successfully!"
            if storage_url:
                message += f"\nStorage URL: {storage_url}"
            send_message(chat_id, message)
        else:
            send_message(chat_id, "📸 Your photo was received, but there was an issue saving it.")
            
        return True
    except Exception as e:
        print(f"Error handling photo: {str(e)}")
        try:
            send_message(update["message"]["chat"]["id"], "Error processing your photo.")
        except:
            print("Could not send error message")
        return False

def handle_document(update):
    """Handle document messages"""
    try:
        chat_id = update["message"]["chat"]["id"]
        user = update["message"]["from"]
        user_id = user.get("id")
        message_id = update["message"].get("message_id")
        document = update["message"]["document"]
        
        # Get document details
        file_id = document.get("file_id")
        file_name = document.get("file_name", "unnamed_document")
        mime_type = document.get("mime_type", "application/octet-stream")
        
        if not file_id:
            print("No file_id found in document")
            return False
            
        print(f"Processing document: {file_name}, type: {mime_type}, file_id: {file_id}")
        
        # Get file info
        file_info = get_file_direct(file_id)
        if not file_info or "file_path" not in file_info:
            print("Could not get file path information")
            send_message(chat_id, "📄 Your document was received, but I couldn't process it.")
            return False
            
        # Download the file
        file_path = file_info["file_path"]
        file_content = download_file_direct(file_path)
        
        if not file_content:
            print("Failed to download document file")
            send_message(chat_id, "📄 Your document was received, but downloading failed.")
            return False
            
        # Save to database
        media_data = {
            "user_id": user_id,
            "message_id": message_id,
            "message_text": f"📄 Document: {file_name}",
            "file_type": "document",
            "file_id": file_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "timestamp": datetime.now().isoformat(),
            "caption": update["message"].get("caption", ""),
            "has_media": True
        }
        
        success, storage_url = save_media_to_supabase(media_data, file_content)
        
        # Send response
        if success:
            message = f"📄 Your document '{file_name}' was received and stored successfully!"
            if storage_url:
                message += f"\nStorage URL: {storage_url}"
            send_message(chat_id, message)
        else:
            send_message(chat_id, f"📄 Your document '{file_name}' was received, but there was an issue saving it.")
            
        return True
    except Exception as e:
        print(f"Error handling document: {str(e)}")
        try:
            send_message(update["message"]["chat"]["id"], "Error processing your document.")
        except:
            print("Could not send error message")
        return False

def handle_video(update):
    """Handle video messages"""
    try:
        chat_id = update["message"]["chat"]["id"]
        user = update["message"]["from"]
        user_id = user.get("id")
        message_id = update["message"].get("message_id")
        video = update["message"]["video"]
        
        # Get video details
        file_id = video.get("file_id")
        duration = video.get("duration", 0)
        width = video.get("width", 0)
        height = video.get("height", 0)
        file_name = video.get("file_name", "video.mp4")
        mime_type = video.get("mime_type", "video/mp4")
        
        if not file_id:
            print("No file_id found in video")
            return False
            
        print(f"Processing video: {file_name}, duration: {duration}s, type: {mime_type}")
        
        # Get file info
        file_info = get_file_direct(file_id)
        if not file_info or "file_path" not in file_info:
            print("Could not get file path information")
            send_message(chat_id, "🎬 Your video was received, but I couldn't process it.")
            return False
            
        # Download the file
        file_path = file_info["file_path"]
        file_content = download_file_direct(file_path)
        
        if not file_content:
            print("Failed to download video file")
            send_message(chat_id, "🎬 Your video was received, but downloading failed.")
            return False
            
        # Save to database
        media_data = {
            "user_id": user_id,
            "message_id": message_id,
            "message_text": f"🎬 Video: {duration}s",
            "file_type": "video",
            "file_id": file_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "duration": duration,
            "width": width,
            "height": height,
            "timestamp": datetime.now().isoformat(),
            "caption": update["message"].get("caption", ""),
            "has_media": True
        }
        
        success, storage_url = save_media_to_supabase(media_data, file_content)
        
        # Send response
        if success:
            message = "🎬 Your video was received and stored successfully!"
            if storage_url:
                message += f"\nStorage URL: {storage_url}"
            send_message(chat_id, message)
        else:
            send_message(chat_id, "🎬 Your video was received, but there was an issue saving it.")
            
        return True
    except Exception as e:
        print(f"Error handling video: {str(e)}")
        try:
            send_message(update["message"]["chat"]["id"], "Error processing your video.")
        except:
            print("Could not send error message")
        return False

def handle_audio(update):
    """Handle audio messages"""
    try:
        chat_id = update["message"]["chat"]["id"]
        user = update["message"]["from"]
        user_id = user.get("id")
        message_id = update["message"].get("message_id")
        audio = update["message"]["audio"]
        
        # Get audio details
        file_id = audio.get("file_id")
        duration = audio.get("duration", 0)
        performer = audio.get("performer", "")
        title = audio.get("title", "")
        file_name = audio.get("file_name", "audio.mp3")
        mime_type = audio.get("mime_type", "audio/mp3")
        
        if not file_id:
            print("No file_id found in audio")
            return False
            
        print(f"Processing audio: {file_name}, duration: {duration}s, title: {title}")
        
        # Get file info
        file_info = get_file_direct(file_id)
        if not file_info or "file_path" not in file_info:
            print("Could not get file path information")
            send_message(chat_id, "🎵 Your audio was received, but I couldn't process it.")
            return False
            
        # Download the file
        file_path = file_info["file_path"]
        file_content = download_file_direct(file_path)
        
        if not file_content:
            print("Failed to download audio file")
            send_message(chat_id, "🎵 Your audio was received, but downloading failed.")
            return False
            
        # Save to database
        media_data = {
            "user_id": user_id,
            "message_id": message_id,
            "message_text": f"🎵 Audio: {title or file_name}",
            "file_type": "audio",
            "file_id": file_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "duration": duration,
            "performer": performer,
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "caption": update["message"].get("caption", ""),
            "has_media": True
        }
        
        success, storage_url = save_media_to_supabase(media_data, file_content)
        
        # Send response
        if success:
            message = f"🎵 Your audio '{title or file_name}' was received and stored successfully!"
            if storage_url:
                message += f"\nStorage URL: {storage_url}"
            send_message(chat_id, message)
        else:
            send_message(chat_id, f"🎵 Your audio was received, but there was an issue saving it.")
            
        return True
    except Exception as e:
        print(f"Error handling audio: {str(e)}")
        try:
            send_message(update["message"]["chat"]["id"], "Error processing your audio.")
        except:
            print("Could not send error message")
        return False

def handle_voice(update):
    """Handle voice messages"""
    try:
        chat_id = update["message"]["chat"]["id"]
        user = update["message"]["from"]
        user_id = user.get("id")
        message_id = update["message"].get("message_id")
        voice = update["message"]["voice"]
        
        # Get voice details
        file_id = voice.get("file_id")
        duration = voice.get("duration", 0)
        mime_type = voice.get("mime_type", "audio/ogg")
        
        if not file_id:
            print("No file_id found in voice")
            return False
            
        print(f"Processing voice message: duration: {duration}s, type: {mime_type}")
        
        # Get file info
        file_info = get_file_direct(file_id)
        if not file_info or "file_path" not in file_info:
            print("Could not get file path information")
            send_message(chat_id, "🎤 Your voice message was received, but I couldn't process it.")
            return False
            
        # Download the file
        file_path = file_info["file_path"]
        file_content = download_file_direct(file_path)
        
        if not file_content:
            print("Failed to download voice file")
            send_message(chat_id, "🎤 Your voice message was received, but downloading failed.")
            return False
            
        # Save to database
        media_data = {
            "user_id": user_id,
            "message_id": message_id,
            "message_text": f"🎤 Voice message: {duration}s",
            "file_type": "voice",
            "file_id": file_id,
            "mime_type": mime_type,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "has_media": True
        }
        
        success, storage_url = save_media_to_supabase(media_data, file_content)
        
        # Send response
        if success:
            message = "🎤 Your voice message was received and stored successfully!"
            if storage_url:
                message += f"\nStorage URL: {storage_url}"
            send_message(chat_id, message)
        else:
            send_message(chat_id, "🎤 Your voice message was received, but there was an issue saving it.")
            
        return True
    except Exception as e:
        print(f"Error handling voice: {str(e)}")
        try:
            send_message(update["message"]["chat"]["id"], "Error processing your voice message.")
        except:
            print("Could not send error message")
        return False

def process_request(request):
    """Process the request and return a response"""
    try:
        # Handle GET requests (health checks)
        if request.get("method", "") == "GET":
            # Test Supabase connection
            supabase_status = test_supabase_connection()
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "ok",
                    "message": "Bot webhook is running (with media support)",
                    "supabase_connected": supabase_status,
                    "supabase_url": SUPABASE_URL
                })
            }
        
        # Handle POST requests (Telegram updates)
        elif request.get("method", "") == "POST":
            body = request.get("body", "{}")
            
            try:
                if isinstance(body, str):
                    update = json.loads(body)
                else:
                    update = body
                
                # Check if we have a message
                if "message" not in update or "chat" not in update["message"]:
                    print("Update doesn't contain a message or chat")
                    return {
                        "statusCode": 200,
                        "body": json.dumps({
                            "status": "ok",
                            "message": "Update processed (no message/chat)"
                        })
                    }
                
                chat_id = update["message"]["chat"]["id"]
                user = update["message"]["from"]
                user_id = user.get("id")
                first_name = user.get("first_name", "")
                last_name = user.get("last_name", "")
                username = user.get("username", "")
                
                # Save user data to Supabase
                user_data = {
                    "user_id": user_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": username
                }
                
                save_user_to_supabase(user_data)
                
                # Check message type and process accordingly
                if "text" in update["message"]:
                    # Process text message
                    text = update["message"]["text"]
                    print(f"Message from {chat_id} (User: {username or first_name}): '{text}'")
                    
                    # Save message to Supabase
                    message_data = {
                        "user_id": user_id,
                        "message_id": update["message"].get("message_id"),
                        "message_text": text,
                        "timestamp": datetime.now().isoformat(),
                        "has_media": False
                    }
                    
                    save_message_to_supabase(message_data)
                    
                    # Handle special commands
                    if text and text.strip() == "/diagnostic":
                        print("Diagnostic command detected!")
                        response_text = get_diagnostic_report(user_id)
                    # Special handling for /start command
                    elif text.strip() == "/start":
                        response_text = "👋 Welcome to the HB Telegram Bot! I'm now active and ready to help you. I can receive and store various media types including photos, documents, videos, audio, and voice messages."
                    else:
                        print("No special command detected")
                        response_text = f"I received: {text}"
                    
                    # Send response using Telegram API
                    if TELEGRAM_TOKEN:
                        try:
                            print(f"Sending response: {response_text[:50]}{'...' if len(response_text) > 50 else ''}")
                            send_message(chat_id, response_text)
                            
                            # Save bot response to Supabase
                            response_data = {
                                "user_id": user_id,
                                "message_id": -1,  # Placeholder for bot message
                                "message_text": response_text,
                                "timestamp": datetime.now().isoformat(),
                                "has_media": False
                            }
                            
                            save_message_to_supabase(response_data)
                            
                        except Exception as e:
                            print(f"Error sending message to user: {e}")
                
                # Handle media messages
                elif "photo" in update["message"]:
                    print("Photo message detected")
                    handle_photo(update)
                elif "document" in update["message"]:
                    print("Document message detected")
                    handle_document(update)
                elif "video" in update["message"]:
                    print("Video message detected")
                    handle_video(update)
                elif "audio" in update["message"]:
                    print("Audio message detected")
                    handle_audio(update)
                elif "voice" in update["message"]:
                    print("Voice message detected")
                    handle_voice(update)
                else:
                    print(f"Unhandled message type: {update['message'].keys()}")
                    send_message(chat_id, "I received your message, but I don't know how to process this type of content yet.")
                
                # Return a success response to Telegram servers
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": "ok",
                        "message": "Update processed successfully"
                    })
                }
            except Exception as e:
                print(f"Error processing request: {e}")
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": "error",
                        "message": str(e)
                    })
                }
        
        # Default response for other methods
        else:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "ok",
                    "message": "Method not supported"
                })
            }
            
    except Exception as e:
        print(f"Global error handler caught: {e}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "error",
                "message": str(e)
            })
        }

# This handler will be called from Vercel
def handler(request, context):
    """Vercel serverless function handler"""
    return process_request(request)

# For local testing
if __name__ == "__main__":
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            request = {"method": "GET"}
            response = process_request(request)
            
            self.wfile.write(response["body"].encode('utf-8'))
        
        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            request = {
                "method": "POST",
                "body": post_data
            }
            
            response = process_request(request)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response["body"].encode('utf-8'))
    
    PORT = 8000
    print(f"Starting server on port {PORT}...")
    httpd = HTTPServer(('localhost', PORT), SimpleHTTPRequestHandler)
    httpd.serve_forever() 