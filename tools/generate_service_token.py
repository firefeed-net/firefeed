#!/usr/bin/env python3

"""Universal service token generator for FireFeed services.
CLI tool to generate JWT tokens matching firefeed_core.auth.token_manager.
"""

import argparse
import jwt
import time
from datetime import timedelta, datetime, timezone
import sys

def generate_token(service_id: str, scopes: list[str], secret_key: str = 'public-api-secret', days: int = 365, issuer: str = 'firefeed-api', algorithm: str = 'HS256') -> str:
    payload = {
        'service_id': service_id,
        'scopes': scopes,
        'iss': issuer,
        'iat': int(time.time()),
        'exp': int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp())
    }
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token

def main():
    parser = argparse.ArgumentParser(description='Generate FireFeed service JWT token')
    parser.add_argument('--service-id', required=True, help='Service ID (e.g. telegram-bot, rss-parser)')
    parser.add_argument('--scopes', nargs='+', default=['health:read', 'internal:health', 'read'], help='Scopes (space separated)')
    parser.add_argument('--days', type=int, default=365, help='Token expiry days')
    parser.add_argument('--secret', default='public-api-secret', help='JWT secret key')
    parser.add_argument('--issuer', default='firefeed-api', help='Token issuer')
    
    args = parser.parse_args()
    
    token = generate_token(args.service_id, args.scopes, args.secret, args.days, args.issuer)
    
    print(f'Generated {args.service_id} token: {token}')
    print(f'\n=== DETAILS ===')
    print(f'Scopes: {args.scopes}')
    print(f'Expires: {datetime.fromtimestamp(int(jwt.decode(token, args.secret, algorithms=[args.issuer])["exp"]), timezone.utc)}')
    
    # Copy to clipboard compat (macOS)
    try:
        import pyperclip
        pyperclip.copy(token)
        print(f'Copied to clipboard!')
    except ImportError:
        print(f'Install pyperclip for clipboard: pip install pyperclip')

if __name__ == '__main__':
    main()

