import os
import uuid

try:
    from supabase import create_client
except ImportError:
    print("supabase is not installed")

def get_client():
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except ImportError:
        pass
        
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("supabase url or key is missing")
        return None
        
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"couldnt connect to supabase: {e}")
        return None

def upload_image(img, prompt, style):
    client = get_client()
    if not client:
        raise ValueError("no supabase client")

    # make a random filename so they dont overwrite each other
    filename = f"{uuid.uuid4()}.png"

    print("uploading to the bucket...")
    try:
        client.storage.from_("generated-images").upload(
            file=img,
            path=filename,
            file_options={"content-type": "image/png"}
        )
    except Exception as e:
        print(f"upload failed: {e}")
        raise RuntimeError(f"upload error: {e}")

    try:
        public_url = client.storage.from_("generated-images").get_public_url(filename)
    except Exception as e:
        print(f"couldnt get url: {e}")
        raise RuntimeError(f"url error: {e}")

    print("saving details to database...")
    record = {
        "filename": filename,
        "prompt": prompt,
        "style": style
    }
    
    try:
        res = client.table("image_history").insert(record).execute()
        
        # add the url and raw image bytes so we can use them right away
        final = res.data[0] if res.data else record
        final["image_url"] = public_url
        final["image"] = img
        return final
        
    except Exception as e:
        print(f"db insert failed: {e}")
        raise RuntimeError(f"db error: {e}")

def fetch_gallery():
    client = get_client()
    if not client:
        return []
        
    try:
        print("grabbing gallery stuff...")
        res = client.table("image_history").select("*").order("created_at", desc=True).limit(20).execute()
        
        images = []
        for row in res.data:
            url = client.storage.from_("generated-images").get_public_url(row["filename"])
            
            images.append({
                "prompt": row["prompt"],
                "style": row["style"],
                "image_url": url,
                "filename": row["filename"],
                "final_prompt": row["prompt"],
                "negative_prompt": "",
                "created_at": row.get("created_at", "")
            })
            
        return images
        
    except Exception as e:
        print(f"failed to fetch gallery: {e}")
        raise RuntimeError(f"gallery error: {e}")

def get_db_stats():
    client = get_client()
    if not client:
        return False, 0, "no keys"
        
    try:
        res = client.table("image_history").select("id", count="exact").execute()
        count = res.count if res.count is not None else len(res.data)
        
        latest = client.table("image_history").select("created_at").order("created_at", desc=True).limit(1).execute()
        time = latest.data[0]["created_at"] if latest.data else "none yet"
        
        if "T" in time:
            time = time.split("T")[0] + " " + time.split("T")[1][:8]
            
        return True, count, time
        
    except Exception as e:
        print(f"stats failed: {e}")
        return False, 0, str(e)
