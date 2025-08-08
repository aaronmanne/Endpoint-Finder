# Changes

## 2025-08-08

### Fixed Parameter Extraction in Java Parser

The Java parser was not correctly extracting all parameters from Java controller methods. The following changes were made to fix this issue:

1. Modified the AST-based parser to extract parameter names from annotation values:
   - Now checks for annotation elements and extracts the actual parameter name from the 'value' attribute
   - Falls back to the variable name if no annotation value is found
   - Added special handling for the Authorization header

2. Modified the regex-based parser to find all parameters in a line:
   - Changed from using `re.search()` to `re.finditer()` to find all matches in a line
   - Updated path, query, header, and cookie parameter extraction to use this approach
   - Now correctly extracts parameter names from annotations when available

These changes ensure that all parameters are correctly extracted from Java controller methods, including when multiple parameters are defined on a single line.

Example:
```java
@GetMapping("/search")
public ResponseEntity<List<PatientSearchDTO>> searchPatients(@RequestHeader(value = "Authorization") String accessToken,
        @RequestParam("org_id") Long orgId, @RequestParam("period_id") Long periodId,
        @RequestParam("collection_id") Long collectionId, @RequestParam("name_group") String nameGroup, @RequestParam("status") String status) {
    return manager.searchPatients(accessToken, orgId, periodId, collectionId, nameGroup, status);
}
```

Before the fix, only some parameters like "orgId" and "accessToken" were extracted. After the fix, all parameters are correctly extracted: "Authorization", "org_id", "period_id", "collection_id", "name_group", and "status".

Note: The existing tests may need to be updated to reflect the improved parameter extraction.