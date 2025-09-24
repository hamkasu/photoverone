/**
 * Simple Node.js script to test PhotoVault API connectivity
 * This verifies that the iOS app can successfully connect to the PhotoVault backend
 */
const axios = require('axios');

// Use the same base URL as the iOS app
const BASE_URL = 'https://cfc6a4a4-df9e-4337-8286-d6a28cb5851b-00-3ngw5jucfqdys.picard.replit.dev';

async function testApiConnection() {
  console.log('🧪 Testing PhotoVault API Connection...');
  console.log(`📡 Base URL: ${BASE_URL}`);
  console.log('');

  try {
    // Test 1: Health check
    console.log('1️⃣ Testing health check endpoint...');
    const healthResponse = await axios.get(`${BASE_URL}/api`, {
      timeout: 10000,
      headers: {
        'User-Agent': 'PhotoVault-iOS-Test/1.0.0',
      }
    });
    
    if (healthResponse.status === 200) {
      console.log('✅ Health check passed');
      console.log(`   Status: ${healthResponse.status}`);
      console.log(`   Response: ${JSON.stringify(healthResponse.data)}`);
    }

    // Test 2: Homepage accessibility
    console.log('');
    console.log('2️⃣ Testing homepage accessibility...');
    const homeResponse = await axios.get(`${BASE_URL}/`, {
      timeout: 10000,
      headers: {
        'User-Agent': 'PhotoVault-iOS-Test/1.0.0',
      }
    });
    
    if (homeResponse.status === 200) {
      console.log('✅ Homepage accessible');
      console.log(`   Status: ${homeResponse.status}`);
      console.log(`   Content-Type: ${homeResponse.headers['content-type']}`);
    }

    // Test 3: Login endpoint (should return method not allowed for GET)
    console.log('');
    console.log('3️⃣ Testing auth endpoints accessibility...');
    try {
      await axios.get(`${BASE_URL}/auth/login`, {
        timeout: 10000,
        headers: {
          'User-Agent': 'PhotoVault-iOS-Test/1.0.0',
        }
      });
    } catch (error) {
      if (error.response && error.response.status === 405) {
        console.log('✅ Login endpoint accessible (method not allowed for GET, as expected)');
      } else if (error.response && error.response.status === 200) {
        console.log('✅ Login endpoint accessible');
      } else {
        throw error;
      }
    }

    console.log('');
    console.log('🎉 All API connectivity tests passed!');
    console.log('📱 The iOS app should be able to connect to PhotoVault successfully.');
    console.log('');
    console.log('📋 Next steps for using the iOS app:');
    console.log('   1. Download/clone this project locally');
    console.log('   2. Run: cd photovault-ios && npm install');
    console.log('   3. Run: npm start');
    console.log('   4. Use Expo Go app or iOS simulator to run the app');
    console.log('   5. The app will connect to the PhotoVault backend automatically');

  } catch (error) {
    console.error('❌ API connection test failed');
    console.error(`   Error: ${error.message}`);
    if (error.response) {
      console.error(`   Status: ${error.response.status}`);
      console.error(`   Response: ${error.response.data}`);
    }
    
    console.log('');
    console.log('🔧 Troubleshooting:');
    console.log('   1. Ensure PhotoVault server is running');
    console.log('   2. Check if the domain URL is correct');
    console.log('   3. Verify network connectivity');
  }
}

testApiConnection();