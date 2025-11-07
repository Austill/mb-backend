# Logging Improvements for Better Debugging

## Current Issue
- User signs in successfully (login POST succeeds)
- Immediately after, GET /api/mood/today returns 401 Unauthorized
- Frontend shows "Failed to load mood data" and redirects to sign-up
- Need better logs to trace token validation and request flow

## Plan
- [x] Add structured logging configuration in config.py
- [x] Add detailed logs in decorators.py for token validation (success/failure)
- [x] Add info logs in routes/auth.py for login success with user context
- [x] Add info logs in routes/mood.py for all requests, especially /today endpoint
- [ ] Add logs in models for database operations if needed
- [ ] Test locally and deploy to verify logs in Render

## Files to Edit
- config.py: Add logging config
- decorators.py: Add token validation logs
- routes/auth.py: Add login success logs
- routes/mood.py: Add request logs

## Expected Outcome
- Logs will show: user login, token validation attempts, mood data requests
- Easier to debug why mood/today gets 401 after successful login
- Structured logs with user_id, request details, timestamps

## Changes Made
- Added LOGGING_LEVEL and LOGGING_FORMAT to config.py (changed to DEBUG for detailed logs)
- Configured logging in __init__.py with basicConfig
- Added detailed token validation logs in decorators.py (success, failure, user_id, request details)
- Added login success log in routes/auth.py with user_id and email
- Added register request logs in routes/auth.py with email and outcome
- Added request logs in routes/mood.py /today endpoint with user_id and outcome
- Added debug logs in models/user.py find_by_id method to trace database queries
- Added additional info log in decorators.py for user data when not found

## Root Cause Analysis
From the logs, the issue is:
1. Login succeeds and returns valid token
2. Token is decoded correctly with user_id
3. But User.find_by_id returns None for that user_id
4. This causes 401 Unauthorized on mood/today request

Possible causes:
- User was deleted between login and mood request
- Database connection issues
- ObjectId conversion problems
- User_id mismatch in token vs database

## Next Steps
- Deploy changes to Render
- Test the sign-in flow again
- Check debug logs for find_by_id calls
- Verify if user exists in database with that ObjectId
