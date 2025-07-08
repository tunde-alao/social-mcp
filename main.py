import re
import os
from typing import Any
import asyncio

import assemblyai as aai
import instaloader
from dotenv import load_dotenv
from mcp.server.stdio import stdio_server
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

# Set AssemblyAI API key from environment variable
if os.getenv("ASSEMBLYAI_API_KEY"):
    aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

mcp = FastMCP("social")


def extract_instagram_url(url: str) -> str:
    """Extract and validate Instagram URL from various Instagram URL formats."""
    # Handle different Instagram URL formats
    patterns = [
        r'(?:instagram\.com/(?:p|reel|tv)/([a-zA-Z0-9_-]+))',
        r'(?:instagram\.com/(?:stories/[^/]+/)?([a-zA-Z0-9_-]+))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return url
    
    raise ValueError(f"Invalid Instagram URL format: {url}")


def extract_shortcode_from_url(url: str) -> str:
    """Extract shortcode from Instagram URL."""
    patterns = [
        r'instagram\.com/(?:p|reel|tv)/([a-zA-Z0-9_-]+)',
        r'instagram\.com/stories/[^/]+/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError(f"Could not extract shortcode from Instagram URL: {url}")


def get_instagram_media_url(instagram_url: str) -> str:
    """
    Extract the direct media URL (CDN link) from Instagram post/reel using instaloader.
    
    Args:
        instagram_url: Instagram post/reel URL
        
    Returns:
        Direct CDN URL to the video/audio content
        
    Raises:
        Exception: If unable to extract media URL or if content is not video/audio
    """
    try:
        # Create instaloader instance
        loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            quiet=True
        )
        
        # Extract shortcode from URL
        shortcode = extract_shortcode_from_url(instagram_url)
        
        # Get post from shortcode
        try:
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
        except Exception as e:
            raise Exception(f"Failed to fetch Instagram post: {str(e)}")
        
        # Check if post has video content
        if not post.is_video:
            raise Exception("Instagram post does not contain video content. Only video content can be transcribed.")
        
        # Get video URL
        video_url = post.video_url
        if not video_url:
            raise Exception("Could not extract video URL from Instagram post.")
        
        return video_url
        
    except Exception as e:
        if "Failed to fetch Instagram post" in str(e) or "Could not extract" in str(e) or "does not contain video" in str(e):
            raise e
        else:
            raise Exception(f"Error extracting Instagram media URL: {str(e)}")


def transcribe_audio_with_assemblyai(audio_url: str, api_key: str = None) -> dict[str, Any]:
    """
    Transcribe audio using AssemblyAI.
    
    Args:
        audio_url: Direct URL to audio/video file
        api_key: AssemblyAI API key (if not set via environment)
        
    Returns:
        Dictionary containing transcription results
    """
    try:
        # Set API key if provided as parameter
        if api_key:
            aai.settings.api_key = api_key
        
        # Check if API key is available
        if not aai.settings.api_key:
            return {
                'success': False,
                'error': 'AssemblyAI API key not found. Please set ASSEMBLYAI_API_KEY environment variable or provide api_key parameter.',
                'audio_url': audio_url
            }
        
        # Configure transcription settings
        config = aai.TranscriptionConfig(
            auto_highlights=True,
            speaker_labels=True,
            language_detection=True,
        )
        
        # Create transcriber and transcribe
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_url, config=config)
        
        if transcript.status == aai.TranscriptStatus.error:
            return {
                'success': False,
                'error': transcript.error,
                'audio_url': audio_url
            }
        
        # Format the transcript with timestamps if available
        formatted_transcript = []
        if transcript.utterances:
            for utterance in transcript.utterances:
                start_time = format_timestamp(utterance.start / 1000)  # Convert ms to seconds
                end_time = format_timestamp(utterance.end / 1000)
                speaker = f"Speaker {utterance.speaker}" if utterance.speaker else "Speaker"
                formatted_transcript.append(f"[{start_time} - {end_time}] {speaker}: {utterance.text}")
        else:
            # Fallback to basic transcript if no utterances
            formatted_transcript.append(transcript.text)
        
        return {
            'success': True,
            'transcript': '\n'.join(formatted_transcript),
            'confidence': transcript.confidence,
            'audio_duration': transcript.audio_duration,
            'language_detected': getattr(transcript, 'language_code', 'unknown'),
            'audio_url': audio_url
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'audio_url': audio_url
        }


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS or HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


@mcp.tool()
async def get_instagram_transcript(url: str, assemblyai_api_key: str = None) -> str:
    """Extract transcript from Instagram video/reel using AssemblyAI.
    
    Args:
        url: Instagram post or reel URL (e.g., https://instagram.com/p/ABC123/ or https://instagram.com/reel/XYZ789/)
        assemblyai_api_key: AssemblyAI API key (optional if ASSEMBLYAI_API_KEY environment variable is set)
    
    Returns:
        The transcript text with timestamps and speaker labels
    """
    try:
        # Validate Instagram URL
        validated_url = extract_instagram_url(url)
        
        # Extract direct media URL from Instagram
        try:
            media_url = get_instagram_media_url(validated_url)
        except Exception as e:
            return f"❌ {str(e)}"
        
        # Transcribe using AssemblyAI
        result = transcribe_audio_with_assemblyai(media_url, assemblyai_api_key)
        
        if result['success']:
            response = f"✅ Successfully extracted transcript from Instagram content\n\n"
            response += f"🔗 Source: {url}\n"
            response += f"🎵 Audio Duration: {result.get('audio_duration', 'Unknown')}ms\n"
            response += f"🌍 Language Detected: {result.get('language_detected', 'Unknown')}\n"
            response += f"📊 Confidence: {result.get('confidence', 'Unknown')}\n\n"
            response += f"📄 Transcript:\n{result['transcript']}"
            
            return response
        else:
            return f"❌ Failed to transcribe content: {result['error']}"
    
    except Exception as e:
        return f"❌ Error processing Instagram content: {str(e)}"


if __name__ == "__main__":
    print("✅ Social MCP Server is now running and ready to process Instagram transcript requests")
    mcp.run(transport='stdio')