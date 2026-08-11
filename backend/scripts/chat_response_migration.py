"""Chat Response Format Migration Script

This script tests and validates the migration from full ChatResponse format to
MVP Structured ChatResponse format per specification: {"reply":"...", "actions":["send_images","send_brochure"]}

It ensures backward compatibility while testing the new structured format.
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add the backend app to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.utils.chat_response_builder import ChatResponseBuilder
from app.schemas.chat_response import StructuredChatResponse, FullChatResponse

class ChatResponseMigration:
    """Migration tool for chat response format changes"""
    
    def __init__(self):
        self.results = {
            "structured_schema": {},
            "full_schema": {},
            "migration_tests": [],
            "format_conversion": [],
            "validation_results": {}
        }
        self.logger = None
    
    def setup_logging(self):
        """Setup logging for migration tests"""
        import logging
        
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('chat_migration.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def test_structured_schema(self) -> dict:
        """Test StructuredChatResponse schema validation"""
        
        print("🧪 Testing StructuredChatResponse Schema")
        print("-" * 50)
        
        test_cases = [
            {
                "name": "Minimal valid response",
                "data": {"reply": "Hello"},
                "should_pass": True
            },
            {
                "name": "Valid response with actions",
                "data": {"reply": "Here are properties", "actions": ["send_images", "send_brochure"]},
                "should_pass": True
            },
            {
                "name": "Invalid: missing reply",
                "data": {"actions": ["send_images"]},
                "should_pass": False
            },
            {
                "name": "Invalid: wrong action type",
                "data": {"reply": "Hello", "actions": ["send_images", 123]},
                "should_pass": False
            },
            {
                "name": "Invalid: actions not a list",
                "data": {"reply": "Hello", "actions": "send_images"},
                "should_pass": False
            }
        ]
        
        results = {}
        passed = 0
        total = len(test_cases)
        
        for test_case in test_cases:
            try:
                response = StructuredChatResponse(**test_case["data"])
                is_valid = True
                
                # Verify data integrity
                if response.reply != test_case["data"]["reply"]:
                    is_valid = False
                
                if "actions" in test_case["data"]:
                    if response.actions != test_case["data"]["actions"]:
                        is_valid = False
                
                actual_pass = is_valid == test_case["should_pass"]
                
                if actual_pass:
                    passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                
                results[test_case["name"]] = {
                    "status": status,
                    "passed": actual_pass,
                    "data": test_case["data"],
                    "response": response.dict() if actual_pass else None
                }
                
                print(f"{status} {test_case['name']}")
                
            except Exception as e:
                results[test_case["name"]] = {
                    "status": "❌ ERROR",
                    "passed": False,
                    "data": test_case["data"],
                    "error": str(e)
                }
                print(f"❌ ERROR {test_case['name']}: {str(e)}")
        
        results["summary"] = {
            "passed": passed,
            "total": total,
            "success_rate": (passed / total * 100) if total > 0 else 0
        }
        
        print(f"\n📊 Schema Test Results: {passed}/{total} ({results['summary']['success_rate']:.1f}%)")
        
        return results
    
    def test_full_schema(self) -> dict:
        """Test FullChatResponse schema validation"""
        
        print("\n🧪 Testing FullChatResponse Schema")
        print("-" * 50)
        
        test_cases = [
            {
                "name": "Valid full format response",
                "data": {
                    "reply": "I found 3 properties",
                    "confidence": 0.85,
                    "actions": [
                        {"type": "send_images", "payload": {"properties": ["prop1"]}},
                        {"type": "send_brochure", "payload": {"project": "Luxe"}}
                    ],
                    "intent": "property_search",
                    "conversation_id": "conv-123",
                    "requires_escalation": False,
                    "metadata": {"agent": "property_agent"}
                },
                "should_pass": True
            },
            {
                "name": "Invalid: missing required fields",
                "data": {
                    "reply": "Hello",
                    "confidence": 0.85
                },
                "should_pass": False
            }
        ]
        
        results = {}
        passed = 0
        total = len(test_cases)
        
        for test_case in test_cases:
            try:
                response = FullChatResponse(**test_case["data"])
                is_valid = True
                
                # Verify critical fields exist
                critical_fields = ["reply", "confidence", "actions", "intent", "conversation_id"]
                for field in critical_fields:
                    if field not in response.dict():
                        is_valid = False
                        break
                
                actual_pass = is_valid == test_case["should_pass"]
                
                if actual_pass:
                    passed += 1
                    status = "✅ PASS"
                else:
                    status = "❌ FAIL"
                
                results[test_case["name"]] = {
                    "status": status,
                    "passed": actual_pass,
                    "data": test_case["data"],
                    "response": response.dict() if actual_pass else None
                }
                
                print(f"{status} {test_case['name']}")
                
            except Exception as e:
                results[test_case["name"]] = {
                    "status": "❌ ERROR",
                    "passed": False,
                    "data": test_case["data"],
                    "error": str(e)
                }
                print(f"❌ ERROR {test_case['name']}: {str(e)}")
        
        results["summary"] = {
            "passed": passed,
            "total": total,
            "success_rate": (passed / total * 100) if total > 0 else 0
        }
        
        print(f"\n📊 Full Schema Test Results: {passed}/{total} ({results['summary']['success_rate']:.1f}%)")
        
        return results
    
    def test_format_conversion(self) -> dict:
        """Test conversion between full and structured formats"""
        
        print("\n🧪 Testing Format Conversion")
        print("-" * 50)
        
        # Simulate LangGraph output data
        raw_graph_data = {
            "agent_reply": "I found 3 BHK apartments in Andheri",
            "agent_actions": [
                {"type": "send_images", "payload": {"properties": ["property1", "property2"]}},
                {"type": "send_brochure", "payload": {"project": "Skyline Residences"}},
                {"type": "schedule_site_visit", "payload": {"date": "2024-01-15"}}
            ],
            "intent": "property_search",
            "confidence": 0.92,
            "conversation_id": "conv-456",
            "requires_escalation": False,
            "metadata": {"agent": "property_agent"}
        }
        
        results = {}
        
        # Test conversion to structured format
        try:
            structured_response = ChatResponseBuilder.build_structured(raw_graph_data)
            
            # Validate structured format
            is_structured_valid = ChatResponseBuilder.validate_structured_format(structured_response)
            
            results["structured_conversion"] = {
                "status": "✅ PASS" if is_structured_valid else "❌ FAIL",
                "response": structured_response,
                "valid": is_structured_valid,
                "actions_count": len(structured_response.get("actions", [])),
                "actions_types": structured_response.get("actions", [])
            }
            
            print(f"{'✅ PASS' if is_structured_valid else '❌ FAIL'} Structured Format Conversion")
            print(f"   Reply: {structured_response['reply'][:50]}...")
            print(f"   Actions: {structured_response.get('actions', [])}")
            print(f"   Valid: {is_structured_valid}")
            
        except Exception as e:
            results["structured_conversion"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
            print(f"❌ ERROR Structured Format Conversion: {str(e)}")
        
        # Test conversion to full format
        try:
            full_response = ChatResponseBuilder.build_full(
                raw_graph_data, 
                raw_graph_data["conversation_id"],
                {"tenant_id": "test-tenant"}
            )
            
            results["full_conversion"] = {
                "status": "✅ PASS",
                "response": full_response,
                "actions_count": len(full_response.get("actions", [])),
                "has_confidence": "confidence" in full_response,
                "has_metadata": "metadata" in full_response
            }
            
            print(f"✅ PASS Full Format Conversion")
            print(f"   Actions: {len(full_response.get('actions', []))}")
            print(f"   Has confidence: {'confidence' in full_response}")
            print(f"   Has metadata: {'metadata' in full_response}")
            
        except Exception as e:
            results["full_conversion"] = {
                "status": "❌ ERROR",
                "error": str(e)
            }
            print(f"❌ ERROR Full Format Conversion: {str(e)}")
        
        return results
    
    def test_mvp_specification(self) -> dict:
        """Test against MVP specification"""
        
        print("\n🧪 Testing MVP Specification Compliance")
        print("-" * 50)
        
        # Test various response patterns against MVP spec
        test_cases = [
            {
                "name": "Simple reply (no actions)",
                "response": {"reply": "Hello, how can I help you today?"},
                "should_pass": True
            },
            {
                "name": "Reply with single action",
                "response": {"reply": "I found properties", "actions": ["send_images"]},
                "should_pass": True
            },
            {
                "name": "Reply with multiple actions",
                "response": {"reply": "Here are options", "actions": ["send_images", "send_brochure", "schedule_call"]},
                "should_pass": True
            },
            {
                "name": "Invalid: actions with non-string elements",
                "response": {"reply": "Hello", "actions": ["send_images", 123]},
                "should_pass": False
            },
            {
                "name": "Invalid: wrong structure",
                "response": {"message": "Hello", "actions": ["send_images"]},
                "should_pass": False
            }
        ]
        
        results = {}
        passed = 0
        total = len(test_cases)
        
        for test_case in test_cases:
            is_valid = ChatResponseBuilder.validate_structured_format(test_case["response"])
            actual_pass = is_valid == test_case["should_pass"]
            
            if actual_pass:
                passed += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            results[test_case["name"]] = {
                "status": status,
                "passed": actual_pass,
                "response": test_case["response"],
                "valid": is_valid,
                "mvp_compliant": test_case["should_pass"]
            }
            
            print(f"{status} {test_case['name']}")
            print(f"   Valid: {is_valid}, MVP Compliant: {test_case['should_pass']}")
        
        results["summary"] = {
            "passed": passed,
            "total": total,
            "success_rate": (passed / total * 100) if total > 0 else 0
        }
        
        print(f"\n📊 MVP Spec Compliance: {passed}/{total} ({results['summary']['success_rate']:.1f}%)")
        
        return results
    
    def run_all_tests(self) -> dict:
        """Run all migration tests"""
        
        print("🚀 Starting Chat Response Format Migration Tests")
        print("=" * 60)
        
        self.setup_logging()
        
        # Run all tests
        self.results["structured_schema"] = self.test_structured_schema()
        self.results["full_schema"] = self.test_full_schema()
        self.results["format_conversion"] = self.test_format_conversion()
        self.results["validation_results"] = self.test_mvp_specification()
        
        # Calculate overall success rate
        total_tests = 0
        total_passed = 0
        
        for test_type, results in self.results.items():
            if "summary" in results:
                total_passed += results["summary"]["passed"]
                total_tests += results["summary"]["total"]
            elif test_type not in ["migration_tests", "format_conversion"]:
                for test_result in results.values():
                    if isinstance(test_result, dict) and "status" in test_result:
                        if "PASS" in test_result["status"]:
                            total_passed += 1
                        total_tests += 1
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        self.results["overall_summary"] = {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "success_rate": overall_success_rate,
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n" + "=" * 60)
        print("📊 OVERALL MIGRATION TEST RESULTS")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Success Rate: {overall_success_rate:.1f}%")
        print(f"Status: {'✅ ALL TESTS PASSED' if overall_success_rate == 100 else '❌ SOME TESTS FAILED'}")
        
        return self.results
    
    def export_results(self, filename: str = "migration_results.json"):
        """Export migration results to JSON file"""
        
        # Create results directory
        results_dir = Path("test_results")
        results_dir.mkdir(exist_ok=True)
        
        # Save results
        with open(results_dir / filename, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results exported to: {results_dir / filename}")


def main():
    """Main migration test function"""
    
    migration = ChatResponseMigration()
    
    try:
        # Run all tests
        results = migration.run_all_tests()
        
        # Export results
        migration.export_results()
        
        # Print summary
        print(f"\n🎉 Migration test completed!")
        print(f"📊 Overall Success Rate: {results['overall_summary']['success_rate']:.1f}%")
        
        if results['overall_summary']['success_rate'] == 100:
            print(f"✅ Ready for production deployment!")
            return 0
        else:
            print(f"❌ Migration tests completed with failures")
            return 1
        
    except Exception as e:
        print(f"❌ Migration test failed: {str(e)}")
        return 1
if __name__ == "__main__":
    exit(main())