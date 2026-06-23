"""
storage.py — Supabase persistence layer for saving and loading images.
"""
import os
import uuid
import logging

logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
except ImportError:
    logger.error("supabase package not installed")
    Client = None

def get_supabase_client():
    """Initializes and returns the Supabase client."""
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except ImportError:
        pass
        
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("DEBUG: SUPABASE_URL or SUPABASE_KEY missing from .env")
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"DEBUG: Failed to initialize Supabase client: {e}")
        return None

def upload_image(image_bytes: bytes, prompt: str, style: str) -> dict:
    """
    Uploads the image to 'generated-images' bucket and saves metadata to 'image_history' table.
    Returns the inserted record or raises an exception on failure.
    """
    client = get_supabase_client()
    if not client:
        raise ValueError("Supabase client not initialized (missing URL/KEY)")

    # Generate a unique filename for the storage bucket
    filename = f"{uuid.uuid4()}.png"

    # 1. Upload to Supabase Storage Bucket
    print(f"DEBUG: Uploading {filename} to 'generated-images' bucket...")
    try:
        upload_res = client.storage.from_("generated-images").upload(
            file=image_bytes,
            path=filename,
            file_options={"content-type": "image/png"}
        )
        print(f"DEBUG: Upload successful.")
    except Exception as e:
        print(f"DEBUG: Upload failed: {e}")
        raise RuntimeError(f"Failed to upload image to bucket: {e}")

    # 2. Get Public URL
    try:
        public_url = client.storage.from_("generated-images").get_public_url(filename)
        print(f"DEBUG: Public URL generated: {public_url}")
    except Exception as e:
        print(f"DEBUG: Failed to get public URL: {e}")
        raise RuntimeError(f"Failed to get public URL: {e}")

    # 3. Insert metadata into Postgres Database
    print(f"DEBUG: Inserting metadata into 'image_history' table...")
    record = {
        "filename": filename,
        "prompt": prompt,
        "style": style
    }
    try:
        db_res = client.table("image_history").insert(record).execute()
        print(f"DEBUG: Database insert successful.")
        
        # Attach the public URL to the returned record for the UI to use
        final_record = db_res.data[0] if db_res.data else record
        final_record["image_url"] = public_url
        final_record["image"] = image_bytes # Keep the bytes for instant download capability
        return final_record
    except Exception as e:
        print(f"DEBUG: Database insert failed: {e}")
        raise RuntimeError(f"Failed to insert metadata into database: {e}")

def fetch_gallery():
    """
    Fetches the latest images from the image_history table.
    """
    client = get_supabase_client()
    if not client:
        print("DEBUG: fetch_gallery aborted, no client.")
        return []
        
    try:
        print("DEBUG: Fetching gallery from Supabase...")
        res = client.table("image_history").select("*").order("created_at", desc=True).limit(20).execute()
        
        records = []
        for row in res.data:
            # Reconstruct the public URL dynamically based on the stored filename
            public_url = client.storage.from_("generated-images").get_public_url(row["filename"])
            
            # Map the database row back to our UI's expected dictionary format
            record = {
                "prompt": row["prompt"],
                "style": row["style"],
                "image_url": public_url,
                "filename": row["filename"],
                "final_prompt": row["prompt"], # We didn't save final_prompt in DB per schema, so use prompt
                "negative_prompt": "",
                "created_at": row.get("created_at", "")
            }
            records.append(record)
            
        print(f"DEBUG: Fetched {len(records)} records.")
        return records
    except Exception as e:
        print(f"DEBUG: Failed to fetch gallery: {e}")
        raise RuntimeError(f"Failed to fetch gallery: {e}")

def get_db_stats():
    """Returns (is_connected: bool, image_count: int, last_timestamp: str)"""
    client = get_supabase_client()
    if not client:
        return False, 0, "No valid Supabase keys"
        
    try:
        # Check connection and get row count
        res = client.table("image_history").select("id", count="exact").execute()
        count = res.count if res.count is not None else len(res.data)
        
        # Get latest timestamp
        latest = client.table("image_history").select("created_at").order("created_at", desc=True).limit(1).execute()
        timestamp = latest.data[0]["created_at"] if latest.data else "No images yet"
        
        # Clean up timestamp format a bit if possible
        if "T" in timestamp:
            timestamp = timestamp.split("T")[0] + " " + timestamp.split("T")[1][:8]
            
        return True, count, timestamp
    except Exception as e:
        print(f"DEBUG: DB stats failed: {e}")
        return False, 0, str(e)
