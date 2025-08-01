"""
Unit tests for the JavaScript parser.
"""

import unittest
from endpoint_finder.parsers.javascript import JavaScriptParser


class TestJavaScriptParser(unittest.TestCase):
    """Test cases for the JavaScript parser."""
    
    def setUp(self):
        """Set up the test case."""
        self.parser = JavaScriptParser()
    
    def test_express_route_detection(self):
        """Test detection of Express.js routes."""
        express_code = """
const express = require('express');
const app = express();

// Basic routes
app.get('/api/users', (req, res) => {
    res.json({ users: [] });
});

app.post('/api/users', (req, res) => {
    res.json({ status: 'created' });
});

// Route with path parameter
app.get('/api/users/:id', (req, res) => {
    res.json({ user: req.params.id });
});

// Multiple HTTP methods
app.put('/api/users/:id', (req, res) => {
    res.json({ status: 'updated' });
});

app.delete('/api/users/:id', (req, res) => {
    res.json({ status: 'deleted' });
});

// Using router
const router = express.Router();

router.get('/products', (req, res) => {
    res.json({ products: [] });
});

router.post('/products', (req, res) => {
    res.json({ status: 'product created' });
});

// Using app.use with router
app.use('/api', router);

// Start the server
app.listen(3000, () => {
    console.log('Server is running on port 3000');
});
"""
        
        endpoints = self.parser.parse(express_code, 'app.js')
        
        # Check that we found 7 endpoints (5 direct app routes + 2 router routes)
        self.assertEqual(len(endpoints), 7)
        
        # Check that the endpoints have the correct paths and methods
        paths = {(endpoint['path'], endpoint['method']) for endpoint in endpoints}
        expected_paths = {
            ('/api/users', 'GET'),
            ('/api/users', 'POST'),
            ('/api/users/:id', 'GET'),
            ('/api/users/:id', 'PUT'),
            ('/api/users/:id', 'DELETE'),
            ('/products', 'GET'),
            ('/products', 'POST')
        }
        self.assertEqual(paths, expected_paths)
        
        # Check that the framework is correctly identified
        for endpoint in endpoints:
            self.assertEqual(endpoint['framework'], 'Express.js')
    
    def test_express_middleware_detection(self):
        """Test detection of Express.js middleware routes."""
        express_middleware_code = """
const express = require('express');
const app = express();

// Middleware for all routes
app.use((req, res, next) => {
    console.log('Request received');
    next();
});

// Middleware for specific path
app.use('/api', (req, res, next) => {
    console.log('API request received');
    next();
});

// Route-specific middleware
app.get('/api/protected', 
    (req, res, next) => {
        // Auth middleware
        next();
    },
    (req, res) => {
        res.json({ data: 'protected' });
    }
);

// Start the server
app.listen(3000);
"""
        
        endpoints = self.parser.parse(express_middleware_code, 'middleware.js')
        
        # Check that we found at least the specific routes
        # Note: Middleware detection can be complex, so we focus on the explicit routes
        paths = {(endpoint['path'], endpoint['method']) for endpoint in endpoints}
        
        # These should definitely be detected
        self.assertIn(('/api/protected', 'GET'), paths)
        self.assertIn(('/api', 'USE'), paths)
        
        # Check that the framework is correctly identified
        for endpoint in endpoints:
            self.assertEqual(endpoint['framework'], 'Express.js')
    
    def test_express_router_detection(self):
        """Test detection of Express.js router routes."""
        express_router_code = """
const express = require('express');
const router = express.Router();

// Define routes on the router
router.get('/', (req, res) => {
    res.json({ message: 'API Home' });
});

router.get('/users', (req, res) => {
    res.json({ users: [] });
});

router.post('/users', (req, res) => {
    res.json({ status: 'created' });
});

// Nested router
const productRouter = express.Router();
productRouter.get('/', (req, res) => {
    res.json({ products: [] });
});

productRouter.get('/:id', (req, res) => {
    res.json({ product: req.params.id });
});

// Mount the nested router
router.use('/products', productRouter);

module.exports = router;
"""
        
        endpoints = self.parser.parse(express_router_code, 'routes.js')
        
        # Check that we found the router routes
        paths = {(endpoint['path'], endpoint['method']) for endpoint in endpoints}
        expected_paths = {
            ('/', 'GET'),
            ('/users', 'GET'),
            ('/users', 'POST'),
            ('/products', 'GET'),
            ('/products/:id', 'GET')
        }
        
        # Check that all expected paths are in the detected paths
        for path in expected_paths:
            self.assertIn(path, paths)
        
        # Check that the framework is correctly identified
        for endpoint in endpoints:
            self.assertEqual(endpoint['framework'], 'Express.js')


if __name__ == '__main__':
    unittest.main()