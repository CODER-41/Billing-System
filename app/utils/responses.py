from flask import jsonify

def success_response(data, status_code=200, message=None):
    body = {'status': 'success', 'data': data}
    if message:
        body['message'] = message
    return jsonify(body), status_code

def error_response(message, status_code=400, errors=None):
    body = {'status': 'error', 'message': message}
    if errors:
        body['errors'] = errors
    return jsonify(body), status_code

def paginated_response(data, total, page, per_page):
    return jsonify({
        'status':   'success',
        'data':     data,
        'total':    total,
        'page':     page,
        'per_page': per_page
    }), 200
