"""
Unit tests for the Java parser.
"""

import unittest
from endpoint_finder.parsers.java import JavaParser


class TestJavaParser(unittest.TestCase):
    """Test cases for the Java parser."""
    
    def setUp(self):
        """Set up the test case."""
        self.parser = JavaParser()
    
    def test_spring_rest_controller_detection(self):
        """Test detection of Spring Boot RestController endpoints."""
        spring_code = """
package com.example.demo.controller;

import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;

@RestController
@RequestMapping("/api")
public class UserController {

    @GetMapping("/users")
    public List<User> getAllUsers() {
        // Implementation
        return userService.findAll();
    }

    @GetMapping("/users/{id}")
    public User getUserById(@PathVariable Long id) {
        // Implementation
        return userService.findById(id);
    }

    @PostMapping("/users")
    public User createUser(@RequestBody User user) {
        // Implementation
        return userService.save(user);
    }
}
"""
        
        endpoints = self.parser.parse(spring_code, 'UserController.java')
        
        # Check that we found 3 endpoints
        self.assertEqual(len(endpoints), 3)
        
        # Check that the endpoints have the correct paths and methods
        paths = {(endpoint['path'], endpoint['method']) for endpoint in endpoints}
        expected_paths = {
            ('/api/users', 'GET'),
            ('/api/users/{id}', 'GET'),
            ('/api/users', 'POST')
        }
        self.assertEqual(paths, expected_paths)
        
        # Check that the framework is correctly identified
        for endpoint in endpoints:
            self.assertEqual(endpoint['framework'], 'Spring Boot')
    
    def test_spring_controller_with_request_mapping(self):
        """Test detection of Spring Boot Controller with RequestMapping endpoints."""
        spring_code = """
package com.example.demo.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
@RequestMapping("/products")
public class ProductController {

    @RequestMapping(method = RequestMethod.GET)
    public String getAllProducts(Model model) {
        // Implementation
        return "products/list";
    }

    @RequestMapping(value = "/{id}", method = RequestMethod.GET)
    public String getProductById(@PathVariable Long id, Model model) {
        // Implementation
        return "products/detail";
    }

    @RequestMapping(value = "/new", method = RequestMethod.GET)
    public String newProductForm(Model model) {
        // Implementation
        return "products/form";
    }

    @RequestMapping(value = "/new", method = RequestMethod.POST)
    public String createProduct(@RequestParam String name, @RequestParam Double price) {
        // Implementation
        return "redirect:/products";
    }
}
"""
        
        endpoints = self.parser.parse(spring_code, 'ProductController.java')
        
        # Check that we found 4 endpoints
        self.assertEqual(len(endpoints), 4)
        
        # Check that the endpoints have the correct paths and methods
        paths = {(endpoint['path'], endpoint['method']) for endpoint in endpoints}
        expected_paths = {
            ('/products', 'GET'),
            ('/products/{id}', 'GET'),
            ('/products/new', 'GET'),
            ('/products/new', 'POST')
        }
        self.assertEqual(paths, expected_paths)
        
        # Check that the framework is correctly identified
        for endpoint in endpoints:
            self.assertEqual(endpoint['framework'], 'Spring Boot')
    
    def test_spring_specialized_mappings(self):
        """Test detection of Spring Boot specialized mapping annotations."""
        spring_code = """
package com.example.demo.controller;

import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PatchMapping;

@RestController
@RequestMapping("/api/items")
public class ItemController {

    @GetMapping
    public List<Item> getAllItems() {
        // Implementation
        return itemService.findAll();
    }

    @GetMapping("/{id}")
    public Item getItemById(@PathVariable Long id) {
        // Implementation
        return itemService.findById(id);
    }

    @PostMapping
    public Item createItem(@RequestBody Item item) {
        // Implementation
        return itemService.save(item);
    }

    @PutMapping("/{id}")
    public Item updateItem(@PathVariable Long id, @RequestBody Item item) {
        // Implementation
        return itemService.update(id, item);
    }

    @PatchMapping("/{id}")
    public Item patchItem(@PathVariable Long id, @RequestBody Map<String, Object> updates) {
        // Implementation
        return itemService.patch(id, updates);
    }

    @DeleteMapping("/{id}")
    public void deleteItem(@PathVariable Long id) {
        // Implementation
        itemService.delete(id);
    }
}
"""
        
        endpoints = self.parser.parse(spring_code, 'ItemController.java')
        
        # Check that we found 6 endpoints
        self.assertEqual(len(endpoints), 6)
        
        # Check that the endpoints have the correct paths and methods
        paths = {(endpoint['path'], endpoint['method']) for endpoint in endpoints}
        expected_paths = {
            ('/api/items', 'GET'),
            ('/api/items/{id}', 'GET'),
            ('/api/items', 'POST'),
            ('/api/items/{id}', 'PUT'),
            ('/api/items/{id}', 'PATCH'),
            ('/api/items/{id}', 'DELETE')
        }
        self.assertEqual(paths, expected_paths)
        
        # Check that the framework is correctly identified
        for endpoint in endpoints:
            self.assertEqual(endpoint['framework'], 'Spring Boot')


if __name__ == '__main__':
    unittest.main()