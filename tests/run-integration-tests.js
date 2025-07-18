const { spawn } = require('child_process');
const chalk = require('chalk');

console.log(chalk.blue('🧪 Running Comprehensive Integration Tests...\n'));

const tests = [
  {
    name: 'API Key Validation',
    command: 'node',
    args: ['./src/utils/security/api-key-audit.js']
  },
  {
    name: 'API Integration Tests',
    command: 'jest',
    args: ['./tests/api/api-integration.test.js', '--verbose']
  },
  {
    name: 'TwitterAPI.io Tests',
    command: 'jest',
    args: ['./tests/api/twitterapiio.test.js', '--verbose']
  },
  {
    name: 'WebSocket Connection Test',
    command: 'node',
    args: ['./tests/websocket-test.js']
  },
  {
    name: 'Dashboard Component Tests',
    command: 'jest',
    args: ['./tests/components', '--verbose']
  }
];

async function runTest(test) {
  return new Promise((resolve, reject) => {
    console.log(chalk.yellow(`\n📋 Running: ${test.name}`));
    console.log(chalk.gray('─'.repeat(50)));
    
    const child = spawn(test.command, test.args, {
      stdio: 'inherit',
      shell: true
    });
    
    child.on('close', (code) => {
      if (code === 0) {
        console.log(chalk.green(`\n✅ ${test.name} - PASSED`));
        resolve();
      } else {
        console.log(chalk.red(`\n❌ ${test.name} - FAILED (exit code: ${code})`));
        reject(new Error(`Test failed: ${test.name}`));
      }
    });
    
    child.on('error', (error) => {
      console.log(chalk.red(`\n❌ ${test.name} - ERROR: ${error.message}`));
      reject(error);
    });
  });
}

async function runAllTests() {
  const results = {
    passed: 0,
    failed: 0,
    errors: []
  };
  
  for (const test of tests) {
    try {
      await runTest(test);
      results.passed++;
    } catch (error) {
      results.failed++;
      results.errors.push({ test: test.name, error: error.message });
    }
  }
  
  // Summary
  console.log(chalk.blue('\n' + '═'.repeat(60)));
  console.log(chalk.blue('TEST SUMMARY'));
  console.log(chalk.blue('═'.repeat(60)));
  console.log(chalk.green(`✅ Passed: ${results.passed}`));
  console.log(chalk.red(`❌ Failed: ${results.failed}`));
  
  if (results.errors.length > 0) {
    console.log(chalk.red('\nFailed Tests:'));
    results.errors.forEach(err => {
      console.log(chalk.red(`  - ${err.test}: ${err.error}`));
    });
  }
  
  console.log(chalk.blue('═'.repeat(60)));
  
  // Exit with appropriate code
  process.exit(results.failed > 0 ? 1 : 0);
}

// Run tests
runAllTests().catch(error => {
  console.error(chalk.red('\n🔥 Test runner failed:'), error);
  process.exit(1);
}); 