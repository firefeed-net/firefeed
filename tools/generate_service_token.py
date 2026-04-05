#!/usr/bin/env python3

"""Universal service token generator for FireFeed services.
CLI tool to generate JWT tokens matching firefeed_core.auth.token_manager.

Security: The secret key must be provided via FIREFEED_JWT_SECRET_KEY environment
variable. Default or weak secrets are not allowed.
"""

import argparse
import jwt
import os
import sys
import time
from datetime import timedelta, datetime, timezone


def generate_token(service_id: str, scopes: list[str], secret_key: str, days: int = 365, issuer: str = 'firefeed-api', algorithm: str = 'HS256') -> str:
    payload = {
        'sub': service_id,  # Subject (service ID) - matches firefeed_core TokenPayload
        'scope': scopes,     # Scopes - matches firefeed_core TokenPayload
        'iss': issuer,
        'iat': int(time.time()),
        'exp': int((datetime.now(timezone.utc) + timedelta(days=days)).timestamp()),
    }
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token


def main():
    parser = argparse.ArgumentParser(
        description='Generate FireFeed service JWT token. '
                    'The secret key must be set via FIREFEED_JWT_SECRET_KEY environment variable.'
    )
    parser.add_argument('--service-id', required=True, help='Service ID (e.g. telegram-bot, rss-parser)')
    parser.add_argument('--scopes', nargs='+', default=['health:read', 'internal:health', 'read'], help='Scopes (space separated)')
    parser.add_argument('--days', type=int, default=365, help='Token expiry days')
    parser.add_argument('--issuer', default='firefeed-api', help='Token issuer')
    # Secret key is now ONLY from environment variable for security
    parser.add_argument('--algorithm', default='HS256', help='JWT signing algorithm')

    args = parser.parse_args()

    # Get secret key from environment variable (required)
    secret_key = os.environ.get('FIREFEED_JWT_SECRET_KEY')
    if not secret_key:
        print("ERROR: FIREFEED_JWT_SECRET_KEY environment variable is required", file=sys.stderr)
        print("Please set it to a secure random string, e.g.:", file=sys.stderr)
        print("  export FIREFEED_JWT_SECRET_KEY=$(openssl rand -hex 32)", file=sys.stderr)
        sys.exit(1)
    
    # Validate secret key strength
    if len(secret_key) < 16:
        print("ERROR: Secret key must be at least 16 characters long", file=sys.stderr)
        sys.exit(1)
    
    if secret_key in ('public-api-secret', 'secret', 'changeme', 'password'):
        print("ERROR: Using default or weak secret keys is not allowed", file=sys.stderr)
        print("Please generate a secure random secret key", file=sys.stderr)
        sys.exit(1)

    token = generate_token(args.service_id, args.scopes, secret_key, args.days, args.issuer, args.algorithm)

    # SECURITY WARNING: Don't print token to stdout which may be logged
    print(f'\n=== TOKEN GENERATED ===', file=sys.stderr)
    print(f'Service: {args.service_id}', file=sys.stderr)
    print(f'Scopes: {args.scopes}', file=sys.stderr)
    print(f'Issuer: {args.issuer}', file=sys.stderr)
    print(f'Algorithm: {args.algorithm}', file=sys.stderr)
    try:
        decoded = jwt.decode(token, secret_key, algorithms=[args.algorithm])
        print(f'Expires: {datetime.fromtimestamp(decoded["exp"], timezone.utc)}', file=sys.stderr)
    except Exception:
        pass
    
    # Write token to file with restricted permissions (600)
    token_file = f"{args.service_id.replace('-', '_')}_token.jwt"
    try:
        import stat
        with open(token_file, 'w') as f:
            f.write(token)
        # Set file permissions to owner read/write only (600)
        os.chmod(token_file, stat.S_IRUSR | stat.S_IWUSR)
        print(f'\n✓ Token written to: {token_file}', file=sys.stderr)
        print(f'⚠ SECURITY: Keep this file secure and delete after use!', file=sys.stderr)
    except Exception as e:
        print(f'\nERROR writing token to file: {e}', file=sys.stderr)
        # Fallback: print token only if file write fails
        print(f'\nTOKEN (save manually):', file=sys.stderr)
        print(token)
    
    # Copy to clipboard (macOS and Linux with xclip/xsel)
    try:
        import pyperclip
        pyperclip.copy(token)
        print(f'\n✓ Copied to clipboard!', file=sys.stderr)
    except ImportError:
        print(f'\nTip: Install pyperclip for clipboard support: pip install pyperclip', file=sys.stderr)
    
    print(f'\n⚠ SECURITY: This token provides long-term access ({args.days} days).', file=sys.stderr)
    print(f'   Store it securely and rotate regularly.', file=sys.stderr)


if __name__ == '__main__':
    main()

