// /scripts/generate-ecdsa-keys.js
const elliptic = require('elliptic');
const ec = new elliptic.ec('secp256k1');

console.log('🔐 Generating ECDSA Keys for Coinbase CDP...\n');

// Generate key pair
const keyPair = ec.genKeyPair();

// Get private key in hex format
const privateKey = keyPair.getPrivate('hex');
const publicKey = keyPair.getPublic('hex');

console.log('Private Key (keep this secret!):', privateKey);
console.log('\nPublic Key:', publicKey);

console.log('\n📝 Add these to your .env file:');
console.log(`COINBASE_ECDSA_PRIVATE_KEY=${privateKey}`);
console.log(`COINBASE_ECDSA_PUBLIC_KEY=${publicKey}`);

console.log('\n⚠️  IMPORTANT: Never commit private keys to version control!'); 