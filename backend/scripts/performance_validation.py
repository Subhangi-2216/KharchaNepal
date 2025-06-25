#!/usr/bin/env python3
"""
Performance validation script for email processing improvements.
Measures and compares performance before and after improvements.
"""
import sys
import os
import time
import statistics
import psutil
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.email_processing.email_parser import EmailExtractor


class PerformanceValidator:
    """Performance validation for email processing improvements."""
    
    def __init__(self):
        self.extractor = EmailExtractor()
        self.results = {}
    
    def log(self, message):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def measure_memory_usage(self):
        """Get current memory usage."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    
    def measure_cpu_usage(self):
        """Get current CPU usage."""
        return psutil.cpu_percent(interval=1)
    
    def benchmark_financial_detection(self, iterations=1000):
        """Benchmark financial email detection performance."""
        self.log(f"Benchmarking financial detection ({iterations} iterations)")
        
        # Test cases representing various email types
        test_cases = [
            {
                "sender": "alerts@nabilbank.com",
                "subject": "Transaction Alert - Rs. 5,000 debited",
                "body": "Your account has been debited with Rs. 5,000 on 15/03/2024"
            },
            {
                "sender": "notifications@paypal.com",
                "subject": "Payment sent",
                "body": "You sent $25.00 to john@example.com"
            },
            {
                "sender": "orders@amazon.com",
                "subject": "Your order has been shipped",
                "body": "Order #123-456789 for $89.99 has been shipped"
            },
            {
                "sender": "newsletter@company.com",
                "subject": "Weekly Newsletter",
                "body": "Check out our latest blog posts and updates"
            },
            {
                "sender": "receipts@uber.com",
                "subject": "Trip receipt",
                "body": "Your trip cost $12.50. Payment charged to card ending in 4567"
            }
        ]
        
        # Warm up
        for case in test_cases[:10]:
            self.extractor.is_financial_email(case["sender"], case["subject"], case["body"])
        
        # Measure performance
        start_memory = self.measure_memory_usage()
        start_time = time.time()
        
        times = []
        for i in range(iterations):
            case = test_cases[i % len(test_cases)]
            
            case_start = time.time()
            is_financial, confidence = self.extractor.is_financial_email(
                case["sender"], case["subject"], case["body"]
            )
            case_end = time.time()
            
            times.append(case_end - case_start)
        
        end_time = time.time()
        end_memory = self.measure_memory_usage()
        
        # Calculate statistics
        total_time = end_time - start_time
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = sorted(times)[int(0.95 * len(times))]
        memory_delta = end_memory - start_memory
        
        results = {
            "total_time": total_time,
            "avg_time_per_email": avg_time * 1000,  # ms
            "median_time_per_email": median_time * 1000,  # ms
            "p95_time_per_email": p95_time * 1000,  # ms
            "emails_per_second": iterations / total_time,
            "memory_delta_mb": memory_delta,
            "iterations": iterations
        }
        
        self.results["financial_detection"] = results
        return results
    
    def benchmark_transaction_extraction(self, iterations=500):
        """Benchmark transaction data extraction performance."""
        self.log(f"Benchmarking transaction extraction ({iterations} iterations)")
        
        # Test cases with various transaction patterns
        test_texts = [
            """
            Dear Customer,
            Your account has been debited with Rs. 5,000.00 on 15/03/2024.
            Transaction ID: TXN123456789
            Merchant: Amazon India
            Available Balance: Rs. 25,000.00
            """,
            """
            Payment Confirmation
            Amount: $89.99
            Date: March 15, 2024
            Merchant: Starbucks Coffee
            Reference: REF987654321
            """,
            """
            Order Receipt
            Total: €125.50
            Order Date: 2024-03-15
            Merchant: Online Store Ltd
            Order ID: ORD-12345-67890
            """,
            """
            Bill Payment Confirmation
            Amount Paid: ¥5,000
            Payment Date: 15/03/2024
            Payee: Tokyo Electric Power
            Transaction Reference: TXN-JP-123456
            """,
            """
            Transfer Confirmation
            Amount: NPR 2,500
            Transfer Date: 15 March 2024
            To: Nepal Electricity Authority
            Reference Number: NCHL123456789
            """
        ]
        
        # Warm up
        for text in test_texts[:5]:
            self.extractor.extract_transaction_patterns(text)
        
        # Measure performance
        start_memory = self.measure_memory_usage()
        start_time = time.time()
        
        times = []
        for i in range(iterations):
            text = test_texts[i % len(test_texts)]
            
            case_start = time.time()
            patterns = self.extractor.extract_transaction_patterns(text)
            case_end = time.time()
            
            times.append(case_end - case_start)
        
        end_time = time.time()
        end_memory = self.measure_memory_usage()
        
        # Calculate statistics
        total_time = end_time - start_time
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = sorted(times)[int(0.95 * len(times))]
        memory_delta = end_memory - start_memory
        
        results = {
            "total_time": total_time,
            "avg_time_per_extraction": avg_time * 1000,  # ms
            "median_time_per_extraction": median_time * 1000,  # ms
            "p95_time_per_extraction": p95_time * 1000,  # ms
            "extractions_per_second": iterations / total_time,
            "memory_delta_mb": memory_delta,
            "iterations": iterations
        }
        
        self.results["transaction_extraction"] = results
        return results
    
    def benchmark_pattern_matching(self, iterations=2000):
        """Benchmark pattern matching performance."""
        self.log(f"Benchmarking pattern matching ({iterations} iterations)")
        
        # Test various pattern types
        test_patterns = [
            ("amount", "Amount: Rs. 1,250.50 has been debited"),
            ("date", "Transaction date: 15/03/2024"),
            ("merchant", "Payment to Amazon.com for $25.99"),
            ("transaction_id", "Transaction ID: TXN123456789"),
            ("currency", "You paid $89.99 to the merchant")
        ]
        
        start_time = time.time()
        
        for i in range(iterations):
            pattern_type, text = test_patterns[i % len(test_patterns)]
            patterns = self.extractor.extract_transaction_patterns(text)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        results = {
            "total_time": total_time,
            "patterns_per_second": iterations / total_time,
            "avg_time_per_pattern": (total_time / iterations) * 1000,  # ms
            "iterations": iterations
        }
        
        self.results["pattern_matching"] = results
        return results
    
    def benchmark_memory_efficiency(self):
        """Test memory efficiency with large datasets."""
        self.log("Testing memory efficiency")
        
        # Force garbage collection
        gc.collect()
        start_memory = self.measure_memory_usage()
        
        # Create large dataset
        large_text = """
        Transaction Alert - Your account has been debited with Rs. 5,000.00 on 15/03/2024.
        Transaction ID: TXN123456789. Merchant: Amazon India. Available Balance: Rs. 25,000.00.
        """ * 1000  # Simulate large email content
        
        # Process multiple times
        for i in range(100):
            is_financial, confidence = self.extractor.is_financial_email(
                "alerts@bank.com",
                "Transaction Alert",
                large_text
            )
            patterns = self.extractor.extract_transaction_patterns(large_text)
        
        # Force garbage collection and measure
        gc.collect()
        end_memory = self.measure_memory_usage()
        memory_delta = end_memory - start_memory
        
        results = {
            "memory_delta_mb": memory_delta,
            "memory_per_operation_kb": (memory_delta * 1024) / 100,
            "large_text_size_kb": len(large_text) / 1024
        }
        
        self.results["memory_efficiency"] = results
        return results
    
    def run_comprehensive_benchmark(self):
        """Run all performance benchmarks."""
        self.log("🚀 Starting Comprehensive Performance Validation")
        
        start_time = time.time()
        
        # Run all benchmarks
        benchmarks = [
            ("Financial Detection", self.benchmark_financial_detection),
            ("Transaction Extraction", self.benchmark_transaction_extraction),
            ("Pattern Matching", self.benchmark_pattern_matching),
            ("Memory Efficiency", self.benchmark_memory_efficiency)
        ]
        
        for name, benchmark_func in benchmarks:
            self.log(f"Running {name} benchmark...")
            try:
                result = benchmark_func()
                self.log(f"✅ {name} benchmark completed")
            except Exception as e:
                self.log(f"❌ {name} benchmark failed: {e}")
                self.results[name.lower().replace(" ", "_")] = {"error": str(e)}
        
        total_time = time.time() - start_time
        self.log(f"All benchmarks completed in {total_time:.2f} seconds")
        
        return self.generate_performance_report()
    
    def generate_performance_report(self):
        """Generate a comprehensive performance report."""
        print("\n" + "="*60)
        print("EMAIL PROCESSING PERFORMANCE VALIDATION REPORT")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Financial Detection Performance
        if "financial_detection" in self.results:
            fd = self.results["financial_detection"]
            print("FINANCIAL EMAIL DETECTION:")
            print(f"  • Average time per email: {fd['avg_time_per_email']:.2f} ms")
            print(f"  • Median time per email: {fd['median_time_per_email']:.2f} ms")
            print(f"  • 95th percentile: {fd['p95_time_per_email']:.2f} ms")
            print(f"  • Throughput: {fd['emails_per_second']:.1f} emails/second")
            print(f"  • Memory delta: {fd['memory_delta_mb']:.2f} MB")
            print()
        
        # Transaction Extraction Performance
        if "transaction_extraction" in self.results:
            te = self.results["transaction_extraction"]
            print("TRANSACTION DATA EXTRACTION:")
            print(f"  • Average time per extraction: {te['avg_time_per_extraction']:.2f} ms")
            print(f"  • Median time per extraction: {te['median_time_per_extraction']:.2f} ms")
            print(f"  • 95th percentile: {te['p95_time_per_extraction']:.2f} ms")
            print(f"  • Throughput: {te['extractions_per_second']:.1f} extractions/second")
            print(f"  • Memory delta: {te['memory_delta_mb']:.2f} MB")
            print()
        
        # Pattern Matching Performance
        if "pattern_matching" in self.results:
            pm = self.results["pattern_matching"]
            print("PATTERN MATCHING:")
            print(f"  • Average time per pattern: {pm['avg_time_per_pattern']:.2f} ms")
            print(f"  • Throughput: {pm['patterns_per_second']:.1f} patterns/second")
            print()
        
        # Memory Efficiency
        if "memory_efficiency" in self.results:
            me = self.results["memory_efficiency"]
            print("MEMORY EFFICIENCY:")
            print(f"  • Memory delta: {me['memory_delta_mb']:.2f} MB")
            print(f"  • Memory per operation: {me['memory_per_operation_kb']:.2f} KB")
            print(f"  • Large text size: {me['large_text_size_kb']:.1f} KB")
            print()
        
        # Performance Assessment
        print("PERFORMANCE ASSESSMENT:")
        
        # Check if performance meets acceptable thresholds
        acceptable = True
        
        if "financial_detection" in self.results:
            fd = self.results["financial_detection"]
            if fd["avg_time_per_email"] > 50:  # 50ms threshold
                print("  ⚠️ Financial detection slower than expected")
                acceptable = False
            else:
                print("  ✅ Financial detection performance acceptable")
        
        if "transaction_extraction" in self.results:
            te = self.results["transaction_extraction"]
            if te["avg_time_per_extraction"] > 100:  # 100ms threshold
                print("  ⚠️ Transaction extraction slower than expected")
                acceptable = False
            else:
                print("  ✅ Transaction extraction performance acceptable")
        
        if "memory_efficiency" in self.results:
            me = self.results["memory_efficiency"]
            if me["memory_delta_mb"] > 50:  # 50MB threshold
                print("  ⚠️ Memory usage higher than expected")
                acceptable = False
            else:
                print("  ✅ Memory usage acceptable")
        
        print()
        
        if acceptable:
            print("🎉 PERFORMANCE VALIDATION PASSED")
            print("The email processing improvements maintain acceptable performance.")
        else:
            print("⚠️ PERFORMANCE CONCERNS DETECTED")
            print("Some performance metrics exceed acceptable thresholds.")
        
        print("="*60)
        
        return acceptable


def main():
    """Main function to run performance validation."""
    validator = PerformanceValidator()
    success = validator.run_comprehensive_benchmark()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
