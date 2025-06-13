import aiofiles
import os

from fastapi import APIRouter, UploadFile, HTTPException

from app.utils.openai import transcribe_audio

router = APIRouter()

@router.post("/audio/transcribe")
async def transcribe(file: UploadFile):
    temp_file_path = f"temp_{file.filename}"
    try:
        async with aiofiles.open(temp_file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        with open(temp_file_path, 'rb') as audio_file:
            transcript = await transcribe_audio(audio_file)
        
        return {"transcription": transcript}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)