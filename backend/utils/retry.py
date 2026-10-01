import time
from functools import wraps

class GeminiServiceError(Exception):
    pass

def with_gemini_retry(request_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            models = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash"]
            
            print(f"{request_name}:")
            for i, model in enumerate(models):
                max_attempts = 1
                attempt = 1
                delay = 1
                
                if i > 0:
                    print(f"Trying fallback {model}...")
                    
                while attempt <= max_attempts:
                    try:
                        kwargs['model_name'] = model
                        result = func(*args, **kwargs)
                        print(f"{model} -> success")
                        kwargs.pop('model_name', None) # clean up
                        return result
                    except Exception as e:
                        error_str = str(e)
                        is_retryable = False
                        
                        if "503" in error_str or "UNAVAILABLE" in error_str:
                            is_retryable = True
                        elif "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                            is_retryable = True
                            
                        if is_retryable:
                            if attempt < max_attempts:
                                time.sleep(delay)
                                attempt += 1
                                delay *= 2
                            else:
                                err_code = "429" if "429" in error_str else "503"
                                print(f"{model} -> {err_code}")
                                break # break the while loop, go to next model
                        else:
                            # Not retryable, raise immediately
                            print(f"{model} -> failed with non-retryable error: {error_str}")
                            raise GeminiServiceError("AI service is temporarily busy. Please try the analysis again in a moment.")
            
            # If we exhausted all models
            raise GeminiServiceError("AI service is temporarily busy. Please try the analysis again in a moment.")
        return wrapper
    return decorator
