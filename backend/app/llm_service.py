import requests
import json
import os
from typing import Dict, Any, Optional
import base64
from PIL import Image
import io

class HuggingFaceLLMService:
    def __init__(self):
        # Using Hugging Face API for document extraction
        # Get your free token at https://huggingface.co/settings/tokens
        self.api_token = os.environ.get('HUGGINGFACE_API_TOKEN', '')
        
        # Debug: Check if token is loaded
        if self.api_token:
            print(f"✓ Hugging Face API token loaded (length: {len(self.api_token)})")
        else:
            print("⚠ Hugging Face API token not found. Using fallback data when API fails.")
            print("  Set HUGGINGFACE_API_TOKEN in .env file to use LLM extraction.")
        
        # Use a text generation model that's good at structured extraction
        # Updated to use new router endpoint (api-inference.huggingface.co is deprecated)
        # Options: mistralai/Mistral-7B-Instruct-v0.2, meta-llama/Llama-2-7b-chat-hf, etc.
        self.api_url = "https://router.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        
        self.headers = {}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"
        
        # Alternative models if primary fails
        self.fallback_urls = [
            "https://router.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf",
            "https://router.huggingface.co/models/google/flan-t5-large"
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def image_to_base64(self, image_path: str) -> str:
        """Convert image to base64 string"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error converting image to base64: {e}")
            return ""
    
    def call_llm_api(self, prompt: str, document_text: str = None) -> Dict[str, Any]:
        """Call Hugging Face API for text generation"""
        try:
            # Construct the full prompt with clear instructions
            full_prompt = f"""<s>[INST] You are an expert at extracting structured data from invoices. Extract the following information from the document text and return ONLY a valid JSON object with this exact structure. Do not include any explanations or additional text.

{{
  "customer_name": "string",
  "customer_email": "string",
  "order_date": "YYYY-MM-DD",
  "invoice_number": "string",
  "total_amount": number,
  "tax_amount": number,
  "shipping_address": "string",
  "billing_address": "string",
  "order_details": [
    {{
      "product_name": "string",
      "product_code": "string",
      "quantity": number,
      "unit_price": number,
      "line_total": number,
      "description": "string"
    }}
  ]
}}

Document text:
{document_text if document_text else prompt}

Return ONLY the JSON object: [/INST]"""

            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "max_new_tokens": 2000,
                    "temperature": 0.1,
                    "return_full_text": False,
                    "top_p": 0.9
                }
            }
            
            # Try primary model first
            urls_to_try = [self.api_url] + self.fallback_urls
            
            for url in urls_to_try:
                try:
                    response = requests.post(
                        url,
                        headers=self.headers,
                        json=payload,
                        timeout=90
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Handle different response formats
                        if isinstance(result, list) and len(result) > 0:
                            generated_text = result[0].get('generated_text', '')
                        elif isinstance(result, dict):
                            generated_text = result.get('generated_text', '')
                        else:
                            generated_text = str(result)
                        
                        if generated_text:
                            parsed = self._parse_json_response(generated_text)
                            if "error" not in parsed:
                                return parsed
                    
                    elif response.status_code == 401:
                        # Unauthorized - likely missing API token
                        print(f"API Error: Unauthorized (401) - Missing or invalid API token for {url}")
                        return {"error": "API authentication failed. Please check your HUGGINGFACE_API_TOKEN or use fallback data."}
                    elif response.status_code == 410:
                        # Gone - endpoint deprecated
                        print(f"API Error: Endpoint deprecated (410) - {url}")
                        error_msg = response.json().get('error', 'Endpoint no longer supported')
                        print(f"  Message: {error_msg}")
                        continue  # Try next model
                    elif response.status_code == 503:
                        # Model is loading, wait and retry
                        print(f"Model {url} is loading, waiting 10 seconds...")
                        import time
                        time.sleep(10)
                        continue
                    else:
                        print(f"API Error for {url}: {response.status_code} - {response.text[:200]}")
                        continue
                        
                except requests.exceptions.Timeout:
                    print(f"Timeout for {url}, trying next model...")
                    continue
                except Exception as e:
                    print(f"Error with {url}: {e}")
                    continue
            
            return {"error": "All API endpoints failed"}
                
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return {"error": str(e)}
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        try:
            # Try to find JSON in the response
            text = text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
            
            # Find JSON object
            start_idx = text.find("{")
            end_idx = text.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # If no JSON found, return error
                return {"error": "No valid JSON found in response", "raw_response": text}
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {"error": f"Failed to parse JSON: {str(e)}", "raw_response": text}
    
    def extract_invoice_data(self, file_path: str, file_type: str = "pdf") -> Dict[str, Any]:
        """Main method to extract invoice data from uploaded file"""
        try:
            # Extract text from document
            if file_type.lower() == "pdf":
                document_text = self.extract_text_from_pdf(file_path)
            else:
                # For images, try to use OCR or describe the image
                # In a production system, you'd use Tesseract OCR or similar
                # For now, we'll try to extract text if it's embedded, or use fallback
                try:
                    # Try to read as text if it's a text-based image format
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        document_text = f.read()
                    if len(document_text.strip()) < 10:
                        document_text = f"Image file uploaded: {file_path}. Please use PDF for better extraction results."
                except:
                    document_text = f"Image file uploaded: {file_path}. Please use PDF for better extraction results."
            
            if not document_text or len(document_text.strip()) < 10:
                return {
                    "error": "Could not extract sufficient text from document. Please ensure the document contains readable text.",
                    "fallback_data": self._generate_fallback_data()
                }
            
            # Call LLM API
            result = self.call_llm_api("", document_text)
            
            # Validate and clean the result
            if "error" in result:
                # Return fallback data if LLM fails
                return {
                    "error": result.get("error"),
                    "fallback_data": self._generate_fallback_data(),
                    "raw_response": result.get("raw_response", "")
                }
            
            # Ensure all required fields are present
            cleaned_data = self._clean_extracted_data(result)
            return cleaned_data
            
        except Exception as e:
            print(f"Error in extract_invoice_data: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "fallback_data": self._generate_fallback_data()
            }
    
    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate extracted data"""
        cleaned = {
            "customer_name": data.get("customer_name", "Unknown Customer"),
            "customer_email": data.get("customer_email", ""),
            "order_date": data.get("order_date", ""),
            "invoice_number": data.get("invoice_number", f"INV-{hash(str(data)) % 10000}"),
            "total_amount": float(data.get("total_amount", 0.0)),
            "tax_amount": float(data.get("tax_amount", 0.0)),
            "shipping_address": data.get("shipping_address", ""),
            "billing_address": data.get("billing_address", ""),
            "order_details": []
        }
        
        # Clean order details
        details = data.get("order_details", [])
        if isinstance(details, list):
            for detail in details:
                if isinstance(detail, dict):
                    cleaned_detail = {
                        "product_name": detail.get("product_name", "Unknown Product"),
                        "product_code": detail.get("product_code", ""),
                        "quantity": int(detail.get("quantity", 1)),
                        "unit_price": float(detail.get("unit_price", 0.0)),
                        "line_total": float(detail.get("line_total", 0.0)),
                        "description": detail.get("description", "")
                    }
                    # Calculate line_total if not provided
                    if cleaned_detail["line_total"] == 0.0:
                        cleaned_detail["line_total"] = cleaned_detail["quantity"] * cleaned_detail["unit_price"]
                    cleaned["order_details"].append(cleaned_detail)
        
        # Calculate total if not provided or incorrect
        if cleaned["total_amount"] == 0.0 and cleaned["order_details"]:
            subtotal = sum(d["line_total"] for d in cleaned["order_details"])
            cleaned["total_amount"] = subtotal + cleaned["tax_amount"]
        
        return cleaned
    
    def _generate_fallback_data(self) -> Dict[str, Any]:
        """Generate sample data if LLM extraction fails"""
        import random
        from datetime import datetime, timedelta
        
        # Generate a more realistic fallback invoice
        invoice_num = f"INV-FALLBACK-{random.randint(1000, 9999)}"
        order_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
        
        # Sample products that might appear in invoices
        sample_products = [
            {"name": "Product XYZ", "code": "23423423", "price": 150.00, "qty": 15},
            {"name": "Product ABC", "code": "45645645", "price": 75.00, "qty": 1},
            {"name": "Web Development Service", "code": "WEB-001", "price": 5000.00, "qty": 1},
            {"name": "Consulting Hours", "code": "CONS-001", "price": 150.00, "qty": 40},
        ]
        
        # Pick 1-3 random products
        selected_products = random.sample(sample_products, random.randint(1, min(3, len(sample_products))))
        
        order_details = []
        subtotal = 0.0
        for product in selected_products:
            line_total = product["price"] * product["qty"]
            subtotal += line_total
            order_details.append({
                "product_name": product["name"],
                "product_code": product["code"],
                "quantity": product["qty"],
                "unit_price": product["price"],
                "line_total": line_total,
                "description": f"Sample {product['name']} description"
            })
        
        tax_rate = 0.06875  # 6.875% like in the sample invoice
        tax_amount = round(subtotal * tax_rate, 2)
        total_amount = subtotal + tax_amount
        
        return {
            "customer_name": "Sample Customer",
            "customer_email": "customer@example.com",
            "order_date": order_date,
            "invoice_number": invoice_num,
            "total_amount": round(total_amount, 2),
            "tax_amount": tax_amount,
            "shipping_address": "123 Main St, City, State, ZIP",
            "billing_address": "123 Main St, City, State, ZIP",
            "order_details": order_details
        }

