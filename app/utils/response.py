from flask import jsonify
from typing import Any, Optional

def success_response(data: Any = None, message: str = 'Success', status_code: int = 200):
    """
    Standard success response format
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
    
    Returns:
        JSON response with standard format
    """
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code



def error_response(message: str, status_code: int = 400, errors: Optional[dict] = None):
    """
    Standard error response format
    
    Args:
        message: Error message
        status_code: HTTP status code
        errors: Additional error details
    
    Returns:
        JSON response with standard format
    """
    response = {
        'success': False,
        'error': message
    }
    
    if errors:
        response['details'] = errors
    
    return jsonify(response), status_code



def paginated_response(items: list, page: int, per_page: int, total: int, message: str = 'Success'):
    """
    Paginated response format
    
    Args:
        items: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        message: Success message
    
    Returns:
        JSON response with pagination metadata
    """
    total_pages = (total + per_page - 1) // per_page
    
    response = {
        'success': True,
        'message': message,
        'data': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_items': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    
    return jsonify(response), 200