# This file is kept for compatibility reasons
# The main functionality has been moved to index.py

# Simply re-export the handler from index.py
try:
    from api.index import handler
except ImportError:
    # If we can't import from api.index, try importing from .index
    try:
        from .index import handler
    except ImportError:
        # Fallback function if imports fail
        def handler(request, context):
            return {
                'statusCode': 500,
                'body': '{"error": "Failed to import handler function"}'
            } 