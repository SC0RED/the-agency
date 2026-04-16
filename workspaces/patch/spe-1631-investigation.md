# SPE-1631 Investigation Report

## Title
"Next page" is broken on Discover page

## Issue Description
On the Discover page (development environment), the first page loads fine, but clicking "Next page" fails with error: "Results are still loading. Please try refreshing in a moment."

## Root Cause Analysis

### Cache Corruption in Assessment Engine
The user's search specification_id `69bdeb030505abb97ff425ac` has a severely corrupted cache entry in MongoDB's `companies_cache` collection.

#### Corrupted Data
- **Document _id**: `df752a5df0b8fb6a93fc9557c934064e75077ead9beeabe378d315866f8ec237`
- **Page 0 metadata**:
  - `pages_complete: 123`
  - `pages_requested: 2`
  - `build_status: building`
  - `thesis_text: present`
- **Page 0 data**: Empty (no companies array)
- **Page 1 cache**: Does NOT exist
- **Pages 2+**: Orphaned/empty records

### How This Breaks Pagination

1. User loads Discover tab with search thesis
2. Engine retrieves page 0 from cache
3. Page 0 validation passes (has thesis_text), metadata shows `pages_complete: 123`
4. Frontend receives `buildPagesComplete = 123`
5. UI renders: "Showing page 1 of 123" and enables "Next" button
6. User clicks "Next" → frontend calls `fetchSearchPage(page=1)`
7. Backend sends to engine: `get_page` operation with `page=1`
8. Engine checks if page 1 exists in cache → **NOT FOUND**
9. Engine returns 202 `page_not_ready` (page not built yet)
10. Frontend retries up to 3×, then shows error: "Results are still loading. Please try refreshing in a moment."

### Why This Happened

**Race Condition in Assessment Engine**: When a search was cancelled or a new search was started, old Lambda invocations from the previous build continued executing. These concurrent Lambdas kept calling `mark_page_complete()` on the same search's page 0 metadata, incrementing `pages_complete` multiple times.

**Increment Pattern Observed**:
- Expected: `pages_complete: 2` (matching `pages_requested: 2`)
- Actual: `pages_complete: 123` (123 out-of-order increments)

This race condition was fixed in the assessment engine at commit `c63b5d4d` (March 23, 2026) by adding `BuildCancelledError` guards in the build status manager. However, the corrupted data already exists in the database.

## Solution

### Immediate Fix (1 SP, Low Risk × Low Intensity)
**Delete the corrupted cache entry** from MongoDB:

```javascript
db.companies_cache.deleteOne({
  _id: "df752a5df0b8fb6a93fc9557c934064e75077ead9beeabe378d315866f8ec237"
})
```

Verify cleanup:
```javascript
db.companies_cache.findOne({
  specification_id: "69bdeb030505abb97ff425ac"
})
// Should return null or only non-corrupted entries
```

### Result
Next time the user loads this search thesis in Discover:
1. Engine no longer finds page 0 in cache
2. Engine performs fresh `start_search` operation
3. Builds all pages with correct `pages_complete` counter
4. Frontend displays correct page count and pagination works normally

### Velocity Impact
- **Weak Positive** — fixes a blocker for this specific user search, but only affects this one corrupted entry

## Prevention
The race condition is already fixed in the engine code (commit c63b5d4d). New searches should not develop this problem.

**Future Monitoring**: If other searches show similar patterns (`pages_complete >> pages_requested` or `pages_complete > 10` with only `pages_requested: 1-2`), they should also be cleared.

## Related Code

### Assessment Engine
- **File**: `src/services/build_status_manager.py`
- **Fix**: Added `BuildCancelledError` exception and null checks on `mark_page_complete()` and `mark_build_complete()` to detect when a search cache was cleared while Lambdas were still running
- **Commit**: c63b5d4d (Mon Mar 23 22:24:57 2026 -0400)

### Frontend Pagination
- **File**: `src/app/modules/search/discover-tab/discover-tab.component.ts` (lines 1089-1143)
- **Method**: `canGoToNextPage` getter
- **Logic**: `buildPagesComplete > tablePage` (checks if next page exists)

### Backend Page Fetch
- **File**: `services/targetListService.js` (lines 1439-1451)
- **Operation**: Path 3 "Page retrieval (default path — fetch cached results)"
- **Engine Call**: POST `/api` with operation `get_page`
- **Response on missing page**: 202 `page_not_ready`

## Estimation

- **Risk**: No Risk (data cleanup only, no code changes)
- **Intensity**: Low (single MongoDB delete operation)
- **Story Points**: 1
- **Business Value**: High (unblocks user's specific search)

## Status
Investigation complete. Awaiting Jira ticket creation and Chris's approval to proceed with data cleanup.
