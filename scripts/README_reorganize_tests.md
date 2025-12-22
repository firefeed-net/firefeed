# Test Structure Reorganization Script

This script automatically reorganizes the test structure in the project, creating a more organized hierarchy that duplicates the main project structure.

## Features

- ✅ Automatic directory structure creation
- ✅ Moving test files to corresponding folders
- ✅ Updating imports in moved files
- ✅ Creating backup copies
- ✅ Dry-run mode for previewing changes
- ✅ Rollback capability

## Usage

### Preview (dry-run)
```bash
python scripts/reorganize_tests.py --dry-run
```

### Perform reorganization
```bash
python scripts/reorganize_tests.py
```

### Rollback changes
```bash
python scripts/reorganize_tests.py --rollback tests_backup_20251222_112446
```

## Target Structure

After reorganization, tests will be organized as follows:

```
tests/
├── apps/
│   ├── api/
│   │   ├── test_api.py
│   │   ├── test_auth.py
│   │   ├── test_models.py
│   │   ├── test_middleware.py
│   │   ├── test_websocket.py
│   │   └── routers/
│   │       ├── test_api_keys.py
│   │       ├── test_categories.py
│   │       ├── test_rss_feeds.py
│   │       ├── test_rss_items_router.py
│   │       ├── test_rss_router.py
│   │       ├── test_telegram.py
│   │       └── test_users.py
│   └── rss_parser/
│       ├── test_rss_fetcher.py
│       ├── test_rss_manager.py
│       ├── test_rss_parser.py
│       ├── test_rss_storage.py
│       ├── test_rss_validator.py
│       └── services/
│           └── test_services.py
├── services/
│   ├── translation/
│   │   └── test_translation_service.py
│   ├── text_analysis/
│   │   └── test_duplicate_detector.py
│   ├── user/
│   │   └── test_user_service.py
│   ├── email/
│   │   ├── test_email.py
│   │   ├── test_email_sender.py
│   │   └── test_registration_success_email.py
│   └── maintenance/
│       └── test_maintenance_service.py
├── repositories/
│   ├── test_user_repository.py
│   ├── test_api_key_repository.py
│   ├── test_category_repository.py
│   ├── test_rss_feed_repository.py
│   └── test_source_repository.py
├── utils/
│   ├── test_utils.py
│   ├── test_utils_api.py
│   ├── test_utils_cleanup.py
│   ├── test_utils_async_mocks.py
│   ├── test_utils_retry.py
│   ├── test_image.py
│   ├── test_image_utils.py
│   ├── test_video.py
│   ├── test_cleanup.py
│   ├── test_cache.py
│   ├── test_retry.py
│   └── test_text.py
├── exceptions/
│   ├── test_cache_exceptions.py
│   ├── test_database_exceptions.py
│   ├── test_service_exceptions.py
│   └── test_exceptions.py
└── integration/
    ├── test_di_integration.py
    ├── test_database.py
    ├── test_database_pool_adapter.py
    ├── test_app.py
    └── test_main.py
```

## Safety

The script automatically:
1. Creates a backup copy of the current test structure
2. Works in transactional mode
3. Verifies the correctness of the result
4. Provides rollback capability

## Recommendations

1. **Always run in dry-run mode first**
2. **Ensure a backup copy is created**
3. **Run tests after reorganization**
4. **Use rollback if problems occur**

## Command Examples

```bash
# Preview changes
python scripts/reorganize_tests.py --dry-run

# Perform reorganization
python scripts/reorganize_tests.py

# Rollback to previous state
python scripts/reorganize_tests.py --rollback tests_backup_20251222_112446

# Check tests after reorganization
python -m pytest tests/ --tb=short -q
```

## Troubleshooting

### Problem: File not found
If the script reports that a file is not found, check:
- Correctness of the file name
- File existence in the tests/ directory
- Possible typos in the name

### Problem: Incorrect imports
After reorganization, some imports may require manual adjustment. The script automatically updates basic import patterns but may miss complex cases.

### Problem: Failing tests
If tests fail after reorganization:
1. Check imports in problematic files
2. Run pytest with verbose output
3. Perform rollback if necessary

## Contacts

For problems or questions, contact the development team.