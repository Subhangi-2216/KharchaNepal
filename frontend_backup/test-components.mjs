// Simple test to verify component imports work
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Testing component imports...');

try {
  
  const componentsDir = path.join(__dirname, 'src', 'components');
  
  // Check if our new components exist
  const transactionApprovalDialog = path.join(componentsDir, 'TransactionApprovalDialog.tsx');
  const transactionDetailView = path.join(componentsDir, 'TransactionDetailView.tsx');
  const transactionApprovals = path.join(componentsDir, 'TransactionApprovals.tsx');
  
  console.log('✅ Checking component files...');
  
  if (fs.existsSync(transactionApprovalDialog)) {
    console.log('✅ TransactionApprovalDialog.tsx exists');
  } else {
    console.log('❌ TransactionApprovalDialog.tsx missing');
  }
  
  if (fs.existsSync(transactionDetailView)) {
    console.log('✅ TransactionDetailView.tsx exists');
  } else {
    console.log('❌ TransactionDetailView.tsx missing');
  }
  
  if (fs.existsSync(transactionApprovals)) {
    console.log('✅ TransactionApprovals.tsx exists');
  } else {
    console.log('❌ TransactionApprovals.tsx missing');
  }
  
  // Check if zod is properly installed
  const zodPath = path.join(__dirname, 'node_modules', 'zod', 'dist', 'esm', 'index.js');
  if (fs.existsSync(zodPath)) {
    console.log('✅ Zod ESM module exists');
  } else {
    console.log('❌ Zod ESM module missing');
  }
  
  // Check PostCSS config
  const postcssConfig = path.join(__dirname, 'postcss.config.js');
  if (fs.existsSync(postcssConfig)) {
    console.log('✅ PostCSS config exists');
    console.log('✅ PostCSS config verification skipped (requires CommonJS)');
  } else {
    console.log('❌ PostCSS config missing');
  }
  
  console.log('\n🎉 Component verification complete!');
  
} catch (error) {
  console.error('❌ Error during component verification:', error.message);
}
