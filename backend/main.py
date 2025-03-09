"""
NOTE: you need to add MongoDB + Gemini credentials 
"""

import json
import os
import traceback
import asyncio
import re
import httpx
import html2text
from typing import List, Dict, Any, Optional, Set
from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl

# Database model for long jobs
class LongJob:
    @staticmethod
    def insert(status, results=None, type=None):
        # Simplified implementation - in a real app, this would interact with a database
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def update_status(job_id, status, results=None):
        # Simplified implementation
        print(f"Updated job {job_id} to status: {status}")
        return True
    
    @staticmethod
    def get_status(job_id, return_object=False):
        # Simplified implementation
        import datetime
        return {
            "status": "completed",
            "type": "deep-find",
            "created_at": datetime.datetime.now().isoformat(),
            "results": {}
        }

# AI API functions
def create_google_request(prompt: str, model_name: str = "gemini-2.0-flash-lite", temperature: float = 1, 
                         top_p: float = 0.95, top_k: int = 40, max_tokens: int = 100, 
                         response_mime_type: str = "text/plain"):
    # Simplified implementation - in a real app, this would call Google's AI API
    try:
        # Mock response for demonstration
        if "definitive_answer_found" in prompt:
            return json.dumps({
                "definitive_answer_found": "false",
                "detailed_explanation": "This is a mock response",
                "other_related_links": []
            })
        return "Mock response from Google AI"
    except Exception as e:
        print(f"Error generating content with Google GenAI: {e}")
        return None

# Create the FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create router
router = APIRouter(
    prefix="/web-app",
    tags=["web-app"],
)

# Request models
class DeepFindReq(BaseModel):
    query: str
    url: HttpUrl
    max_links: Optional[int] = 200
    check_interval: Optional[int] = 50
    tenant_name: Optional[str] = None

# HTML to text conversion
def html_to_text(html, ignore_links=False, bypass_tables=False, ignore_images=True):
    '''
    This function is used to convert html to text.
    
    Args:
        html (str): The HTML content to convert to text.
        ignore_links (bool): Ignore links in the text.
        bypass_tables (bool): Bypass tables in the text.
        ignore_images (bool): Ignore images in the text.
    Returns:
        str: The text content of the webpage.
    '''
    text = html2text.HTML2Text()
    text.ignore_links = ignore_links
    text.bypass_tables = bypass_tables
    text.ignore_images = ignore_images
    return text.handle(html)

async def get_website_url_content(url: HttpUrl, ignore_links: bool = False, max_length: int = None, tenant_name:str=None):
    '''
    This function is used to scrape a webpage.
    It converts the html to text and returns the text.
    
    Args:
        url (HttpUrl): The URL to scrape.
        ignore_links (bool): Whether to ignore links in the output.
        max_length (int): Maximum length of text to return.
        tenant_name (str): Optional tenant name for tracking.

    Returns:
        str: The text content of the webpage.
    '''
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(str(url), headers=header, timeout=5)
    except Exception as e:
        print('Error in webscrape: ', e)
        return "Error fetching the url "+str(url)
    out = html_to_text(response.text, ignore_links=ignore_links)
    if max_length:
        return out[0:max_length]
    else:
        return out

max_characters_form_web_page = 500000
max_characters_for_final_check = 800000

async def check_content_with_ai(content: str, search_query: str, link_count: int, is_final: bool = False, accumulated_text: Optional[str] = None) -> Dict[str, Any]:
    '''
    Checks the content with Google's AI to see if it contains the answer to the search query.
    
    Args:
        content (str): The text from the current web page or accumulated text if is_final is True.
        search_query (str): The query to search for in the content.
        link_count (int): The number of links processed so far.
        is_final (bool): Whether this is the final check using accumulated text.
        accumulated_text (Optional[str]): The accumulated text from all crawled pages, used only if is_final is True.
        
    Returns:
        Dict[str, Any]: The parsed AI response containing definitive_answer_found, answer, and other_related_links.
    '''
    text_to_check = accumulated_text if is_final else content
    max_chars = max_characters_for_final_check if is_final else max_characters_form_web_page
    
    prompt = f"""
    I have collected text from {'multiple web pages' if is_final else 'a web page'}. Here's the information:
    
    {text_to_check[:max_chars]} 
    Based on this information, please answer the following question in JSON format.:
    {search_query}

    Only return true if the answer is definitely and precisely found in the text. If there is missing information, we will continue crawling so return false.
    If a definitive answer is found, give a detailed explanation back of the answer using the information. Incorporate all the related information as well as any other information even though the user didn't ask for it.

    Use this JSON schema:

    Answer = {{'definitive_answer_found': str, 'detailed_explanation': str, 'other_related_links': list[str]}}
    Return: Answer
    """
    
    ai_response = create_google_request(
        prompt=prompt,
        model_name="gemini-2.0-flash-lite",
        temperature=0.2,
        max_tokens=500,
        response_mime_type="application/json"
    )

    print("AI RESPONSE: ", ai_response)
        
    # Parse the JSON response
    try:
        parsed_response = json.loads(ai_response)
        return parsed_response
    except json.JSONDecodeError:
        print("Error parsing AI response: ", ai_response)
        # Return a default structure if parsing fails
        return {
            "definitive_answer_found": "false",
            "detailed_explanation": "Failed to parse AI response",
            "other_related_links": []
        }

def extract_links_from_text(text: str) -> List[str]:
    '''
    Extracts links from markdown text produced by html2text.
    
    Args:
        text (str): The markdown text to extract links from.
        
    Returns:
        List[str]: A list of extracted links.
    '''
    # Pattern to match markdown links: [text](url)
    markdown_links = re.findall(r'\[.*?\]\((.*?)\)', text)
    
    # Pattern to match bare URLs
    bare_urls = re.findall(r'(?<!\()(https?://[^\s\)]+)(?!\))', text)
    
    # Combine and remove duplicates
    all_links = list(set(markdown_links + bare_urls))
    
    return all_links

async def crawl_website_for_information(start_url: HttpUrl, search_query: str, max_links: int = 200, check_interval: int = 50, tenant_name: str = None):
    '''
    Crawls a website starting from the given URL, follows outgoing links, and accumulates text.
    Periodically checks if the current page content contains the answer to the search query using Google's AI.
    Also uses AI to filter which links to follow based on relevance to the search query.
    
    Args:
        start_url (HttpUrl): The starting URL to begin crawling from.
        search_query (str): The query to search for in the accumulated text.
        max_links (int): Maximum number of links to crawl. Default is 200.
        check_interval (int): How often to check with Google's AI (in number of links). Default is 50.
        tenant_name (str): Optional tenant name for tracking purposes.
        
    Returns:
        Dict: A dictionary containing the accumulated text, visited URLs, and the AI's response.
    '''
    visited_urls: Set[str] = set()
    to_visit: List[str] = [str(start_url)]
    accumulated_text: str = ""
    results: Dict[str, Any] = {
        "visited_urls": [],
        "accumulated_text": "",
        "ai_responses": []
    }
    
    link_count = 0
    
    while to_visit and link_count < max_links:
        current_url = to_visit.pop(0)
        
        # Skip if already visited
        if current_url in visited_urls:
            continue
            
        print(f"Crawling: {current_url} ({link_count + 1}/{max_links})")
        
        # Get content from the URL
        content = await get_website_url_content(current_url, ignore_links=False, tenant_name=tenant_name)
        
        # Mark as visited
        visited_urls.add(current_url)
        results["visited_urls"].append(current_url)
        link_count += 1
        
        # Add content to accumulated text
        accumulated_text += f"\n\n--- Content from {current_url} ---\n\n{content}"
        
        # Check current page content with AI
        ai_response = await check_content_with_ai(content, search_query, link_count)
        
        results["ai_responses"].append({
            "url": current_url,
            "links_processed": link_count,
            "response": ai_response
        })

        # If AI found a definitive answer, we can stop crawling
        if ai_response and ai_response.get("definitive_answer_found", "").lower() == "true":
            print(f"Answer found after processing {link_count} links")
            print("FINAL AI RESPONSE: ", ai_response)
            return {
                "link": current_url,
                "ai_response": ai_response
            }
        
        # Extract links from the content
        all_links = extract_links_from_text(content)
        
        # Filter out already visited links
        new_links = [link for link in all_links if link not in visited_urls and link not in to_visit]
        
        # Convert relative links to absolute
        processed_links = []
        for link in new_links:
            if not link.startswith(('http://', 'https://')):
                # Try to construct absolute URL
                base_url = '/'.join(current_url.split('/')[:3])  # Get domain part
                if link.startswith('/'):
                    link = f"{base_url}{link}"
                else:
                    path_parts = current_url.split('/')
                    if len(path_parts) > 3:
                        parent_path = '/'.join(path_parts[:-1])
                        link = f"{parent_path}/{link}"
                    else:
                        link = f"{base_url}/{link}"
            processed_links.append(link)
        
        # Use AI to filter links for relevance
        if processed_links:
            filter_prompt = f"""The user is looking for {search_query}
The links to visit are: {processed_links}
Return the links that would be relevant to what they might be looking for and only return the links that point to more information websites (filter out links to home page, footer, navbar, etc.)

Use this JSON schema:
Return: list[str]"""

            try:
                ai_link_response = create_google_request(
                    prompt=filter_prompt,
                    model_name="gemini-2.0-flash-lite",
                    temperature=0.2,
                    max_tokens=1000,
                    response_mime_type="application/json"
                )
                
                if ai_link_response:
                    try:
                        filtered_links = json.loads(ai_link_response)
                        if isinstance(filtered_links, list):
                            to_visit.extend(filtered_links)
                            print(f"AI filtered links from {len(processed_links)} to {len(filtered_links)}")
                        else:
                            # Fallback if AI didn't return a list
                            to_visit.extend(processed_links)
                    except json.JSONDecodeError:
                        # Fallback if AI didn't return valid JSON
                        to_visit.extend(processed_links)
                else:
                    # Fallback if AI didn't respond
                    to_visit.extend(processed_links)
            except Exception as e:
                print(f"Error filtering links with AI: {e}")
                # Fallback to using all links
                to_visit.extend(processed_links)
    
    # Final check with accumulated text if we've processed all links or reached the limit
    final_ai_response = await check_content_with_ai("", search_query, link_count, is_final=True, accumulated_text=accumulated_text)
    
    results["ai_responses"].append({
        "links_processed": link_count,
        "is_final": True,
        "response": final_ai_response
    })
    
    results["accumulated_text"] = accumulated_text
    return final_ai_response if final_ai_response.get("definitive_answer_found", "").lower() == "true" else results

async def process_deep_find(
    url: HttpUrl, 
    query: str, 
    max_links: int, 
    check_interval: int, 
    tenant_name: str,
    long_job_id: str
):
    """
    Background task to process the deep find request and update the long job status.
    """
    try:
        # Update job status to processing
        LongJob.update_status(long_job_id, "processing")
        
        # Call the crawl function
        result = await crawl_website_for_information(
            url, 
            query, 
            max_links=max_links, 
            check_interval=check_interval, 
            tenant_name=tenant_name
        )
        
        # Update the long job with the results
        LongJob.update_status(long_job_id, "completed", result)
        
    except Exception as e:
        print(f"Error in deep find process: {str(e)}")
        traceback.print_exc()
        # Update job status to error
        LongJob.update_status(long_job_id, "error", {"error": str(e)})

# Routes
@router.post("/deep-find")
async def deep_find(req: DeepFindReq, background_tasks: BackgroundTasks):
    """
    Performs a deep search on a website to find information related to a query.
    Uses background tasks and long job tracking for asynchronous processing.
    """
    try:
        # Create a long job to track the progress
        long_job_id = LongJob.insert('started', [], type='deep-find')
        
        # Add the crawl task to background tasks
        background_tasks.add_task(
            process_deep_find,
            req.url,
            req.query,
            req.max_links,
            req.check_interval,
            req.tenant_name,
            long_job_id
        )
        
        return {"message": "Deep find search started", "long_job_id": long_job_id}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error starting deep find: {str(e)}")

@router.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a long-running job and its results if completed.
    
    Args:
        job_id: The ID of the long job to check
        
    Returns:
        JSON response with job status and results if available
    """
    try:
        # Get the job data with full object
        job_data = LongJob.get_status(job_id, return_object=True)
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
            
        # Return the job status and results
        return {
            "status": job_data.get("status"),
            "type": job_data.get("type", ""),
            "created_at": job_data.get("created_at"),
            # Only include results if the job is completed
            "results": job_data.get("results") if job_data.get("status") == "completed" else None,
            "error": job_data.get("results", {}).get("error") if job_data.get("status") == "error" else None
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error retrieving job status: {str(e)}")

# Include router in app
app.include_router(router)

# Root route
@app.get("/")
async def root():
    return {"message": "Deep Find API"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)