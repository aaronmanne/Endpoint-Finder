#!/usr/bin/env python3
import os
import json
from endpoint_finder.parsers.java import JavaParser
from endpoint_finder.openapi import generate_openapi_spec

# Example Java code from the issue description
JAVA_CODE = '''
@RestController
@RequestMapping("/api/patients")
public class PatientController {
    @Autowired
    private PatientManager manager;
    
    @GetMapping("/search")
    public ResponseEntity<List<PatientSearchDTO>> searchPatients(@RequestHeader(value = "Authorization") String accessToken,
            @RequestParam("org_id") Long orgId, @RequestParam("period_id") Long periodId,
            @RequestParam("collection_id") Long collectionId, @RequestParam("name_group") String nameGroup, @RequestParam("status") String status) {
        return manager.searchPatients(accessToken, orgId, periodId, collectionId, nameGroup, status);
    }
}
'''

def main():
    # Parse the Java code
    parser = JavaParser()
    endpoints = parser.parse(JAVA_CODE, "test_file.java")
    
    # Print the extracted endpoints
    print("Extracted endpoints:")
    for endpoint in endpoints:
        print(f"Path: {endpoint['path']}")
        print(f"Method: {endpoint['method']}")
        print(f"Query parameters: {endpoint['query_params']}")
        print(f"Header parameters: {endpoint['header_params']}")
        print()
    
    # Generate OpenAPI spec
    spec = generate_openapi_spec(endpoints, "test-repo")
    
    # Print the OpenAPI spec
    print("\nGenerated OpenAPI spec:")
    print(json.dumps(spec, indent=2))
    
    # Check if all parameters are included
    expected_params = ["org_id", "period_id", "collection_id", "name_group", "status", "Authorization"]
    found_params = []
    
    # Extract all parameters from the spec
    for path, path_obj in spec["paths"].items():
        for method, method_obj in path_obj.items():
            for param in method_obj.get("parameters", []):
                found_params.append(param["name"])
    
    # Check if all expected parameters are found
    missing_params = [param for param in expected_params if param not in found_params]
    if missing_params:
        print(f"\nMISSING PARAMETERS: {missing_params}")
    else:
        print("\nAll expected parameters were found!")

if __name__ == "__main__":
    main()