import json
import os
import re
import base64
import io
import traceback
import random
from typing import Dict, Any
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance
import PyPDF2

class GoogleLLMService:
    def __init__(self):
        """Initialize Google LLM Service using generative AI API"""
        self.apiKey = os.environ.get('GOOGLE_API_KEY', '')
        self.clientAvailable = False
        self.easyocrAvailable = False
        
        # Check for EasyOCR
        try:
            import easyocr
            self.easyocr = easyocr
            self.ocrReader = None 
            self.easyocrAvailable = True
        except Exception as e:
            print(f"⚠ EasyOCR not available: {e}")
        
        if self.apiKey:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.apiKey)
                self.genai = genai
                
                self.modelName = self._findAvailableModel()
                self.clientAvailable = bool(self.modelName)
                
                if self.modelName:
                    print(f"✓ Google Generative AI API token loaded (using {self.modelName})")
                else:
                    print("⚠ Could not find available model for content generation")
            except ImportError:
                print("⚠ google-generativeai package not found. Install with: pip install google-generativeai")
            except Exception as e:
                print(f"⚠ Error initializing Google API: {e}")
        else:
            print("⚠ Google API key not found. Using fallback data when API fails.")
           
        self.generationConfig = {
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 4000,
        }
        
        self.safetySettings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    
    def _findAvailableModel(self) -> str:
        """Find an available model for content generation"""
        modelsToTry = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash-001",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite-001",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash-latest"
        ]
        
        try:
            # List all available models
            availableModels = self.genai.list_models()

            # Try preferred models first
            modelNames = [m.name.split('/')[-1] for m in availableModels]
            for model in modelsToTry:
                if model in modelNames:
                    return model
            for model in availableModels:
                if "generateContent" in [method.name for method in model.supported_generation_methods]:
                    return model.name.split('/')[-1]
            
            return None
        except Exception as e:
            print(f"Error finding available model: {e}")
            return "gemini-2.5-flash"
    
    def extractTextFromImage(self, imagePath: str) -> str:
        """Extract text from image using EasyOCR"""
        if not self.easyocrAvailable:
            print("⚠ EasyOCR not available, attempting Gemini vision extraction")
            return self._extractViaGeminiVision(imagePath)
        
        try:
            # Initialize OCR reader lazily (first time only)
            if self.ocrReader is None:
                print("Initializing EasyOCR reader...")
                self.ocrReader = self.easyocr.Reader(['en'], gpu=False)
            

            result = self.ocrReader.readtext(imagePath)
            text = "\n".join([line[1] for line in result if line[1]])
            
            if text and len(text.strip()) > 10:
                print(f"✓ Extracted {len(text)} characters from image using EasyOCR")
                return text
            else:
                print("⚠ Image OCR returned insufficient text, trying Gemini vision")
                return self._extractViaGeminiVision(imagePath)
        except Exception as e:
            print(f"Error with EasyOCR: {e}, falling back to Gemini vision")
            return self._extractViaGeminiVision(imagePath)
    
    def extractTextFromPdf(self, pdfPath: str) -> str:
        """Extract text from PDF - tries text extraction first, then OCR if needed"""
        try:
            text = ""
            
            # First, try standard text extraction (for text-based PDFs)
            try:
                with open(pdfPath, 'rb') as file:
                    pdfReader = PyPDF2.PdfReader(file)
                    for page in pdfReader.pages:
                        pageText = page.extract_text()
                        if pageText:
                            text += pageText + "\n"
            except Exception as e:
                print(f"Standard PDF extraction failed: {e}")
            
            # If we got enough text, return it
            if text and len(text.strip()) > 100:
                print(f"✓ Extracted {len(text)} characters from PDF using text extraction")
                return text
            
            # If text extraction didn't work well, try OCR with EasyOCR
            if self.easyocrAvailable:
                try:
                    try:
                        from pdf2image import convert_from_path
                    except ImportError:
                        print("pdf2image not installed. Install with: pip install pdf2image")
                        raise
                    
                    print("Attempting EasyOCR on PDF pages...")
                    # Initialize OCR reader if not already done
                    if self.ocrReader is None:
                        self.ocrReader = self.easyocr.Reader(['en'], gpu=False)
                    
                    pages = convert_from_path(pdfPath, first_page=1, last_page=5)
                    
                    ocrText = ""
                    for pageNum, page in enumerate(pages, 1):
                        result = self.ocrReader.readtext(page)
                        pageText = "\n".join([line[1] for line in result if line[1]])
                        if pageText:
                            ocrText += f"--- Page {pageNum} ---\n{pageText}\n"
                    
                    if ocrText and len(ocrText.strip()) > 100:
                        print(f"✓ Extracted {len(ocrText)} characters from PDF using EasyOCR")
                        return ocrText
                except Exception as e:
                    print(f"PDF OCR extraction failed: {e}")
            
            if text:
                print(f"⚠ PDF extraction returned {len(text)} characters (limited)")
                return text
            else:
                print("⚠ Could not extract text from PDF")
                return ""
                
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def _extractViaGeminiVision(self, imagePath: str) -> str:
        """Use Gemini's vision API to extract text from image"""
        if not self.clientAvailable:
            print("⚠ Google API not available for vision extraction")
            return ""
        
        try:
            # Read image and encode as base64
            with open(imagePath, 'rb') as imgFile:
                imageData = base64.standard_b64encode(imgFile.read()).decode('utf-8')
            
            # Determine image type
            fileExt = imagePath.lower().split('.')[-1]
            mimeTypeMap = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            mimeType = mimeTypeMap.get(fileExt, 'image/jpeg')
            
            # Use Gemini to extract text from image
            model = self.genai.GenerativeModel(self.modelName)
            
            prompt = """Extract all visible text from this document/invoice image. Return only the extracted text, nothing else."""
            
            response = model.generate_content([
                {
                    "mime_type": mimeType,
                    "data": imageData
                },
                prompt
            ])
            
            if response and response.text:
                text = response.text.strip()
                print(f"✓ Extracted {len(text)} characters using Gemini vision API")
                return text
            else:
                print("⚠ No text extracted from image via Gemini")
                return ""
                
        except Exception as e:
            print(f"Error with Gemini vision extraction: {e}")
            return ""
    
    def extractTextFromDocument(self, filePath: str, fileType: str) -> str:
        """Extract text from any document type"""
        print(f"Extracting text from {fileType.upper()} file...")
        
        if fileType.lower() == "pdf":
            return self.extractTextFromPdf(filePath)
        else:
            # For images
            return self.extractTextFromImage(filePath)
    
    def callLlmApi(self, documentText: str) -> Dict[str, Any]:
        """Call Google Generative AI API for text generation"""
        if not self.clientAvailable:
            return {"error": "Google API not available"}
        
        try:
            prompt = f"""You are a professional document processing AI specialized in invoice data extraction. Your task is to analyze the provided document text and extract structured information as a valid JSON object.

CRITICAL INSTRUCTIONS:
1. Return ONLY a complete and valid JSON object - no additional text, markdown, or code blocks
2. MUST start with '{{' and MUST end with '}}'
3. ALL closing braces }} and brackets ] MUST be included - do not truncate
4. If a field cannot be found, use empty string "" for text and 0 for numbers
5. All required fields must be present in the output
6. Parse dates to ISO format (YYYY-MM-DD)
7. Amounts are numbers only, no currency symbols

REQUIRED DATA STRUCTURE:
{{
  "customer_name": "string (full name or company name)",
  "customer_email": "string (email address)",
  "order_date": "string (format: YYYY-MM-DD)",
  "invoice_number": "string (invoice/receipt number)",
  "total_amount": number (total payable amount as float/integer without currency symbol),
  "tax_amount": number (tax amount as float/integer without currency symbol),
  "shipping_address": "string (complete shipping address)",
  "billing_address": "string (complete billing address)",
  "order_details": [
    {{
      "product_name": "string (name of product/item)",
      "product_code": "string (SKU/product code)",
      "quantity": number (integer quantity),
      "unit_price": number (price per unit as float/integer),
      "line_total": number (quantity × unit_price as float/integer),
      "description": "string (product description)"
    }}
  ]
}}

EXTRACTION GUIDELINES:
- "customer_name": Look for "Bill To:", "Customer:", "Client:", "Name:" or similar
- "customer_email": Look for "Email:", "@" symbol patterns
- "order_date": Look for "Date:", "Invoice Date:", "Order Date:" - convert to YYYY-MM-DD
- "invoice_number": Look for "Invoice #:", "Receipt #:", "Order #:" 
- "total_amount": Look for "Total:", "Amount Due:", "Grand Total:" - extract numeric value only
- "tax_amount": Look for "Tax:", "VAT:", "GST:", "Tax Amount:" - extract numeric value only
- "shipping_address": Look for "Ship To:", "Delivery Address:", "Shipping:" 
- "billing_address": Look for "Bill To:", "Billing Address:", "Invoice Address:"
- "order_details": Extract line items, typically in a table format with product information

DOCUMENT TEXT TO PROCESS:
{documentText[:4000]}

Return ONLY the complete, valid JSON object with ALL closing braces and brackets. Do not truncate or omit any closing characters."""

            model = self.genai.GenerativeModel(
                model_name=self.modelName,
                generation_config=self.generationConfig,
                safety_settings=self.safetySettings
            )
            
            response = model.generate_content(prompt)
            
            if response and response.text:
                print("✓ Got response from Google Generative AI")
                print(f"Response preview: {response.text}")
                parsed = self._parseJsonResponse(response.text)
                return parsed
            else:
                return {"error": "No response from Google API"}
                
        except Exception as e:
            print(f"Error calling Google Generative AI: {e}")
            return {"error": str(e)}
    
    def _parseJsonResponse(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        try:
            text = text.strip()           
            if text.startswith("```"):
                newline_idx = text.find("\n")
                if newline_idx != -1:
                    text = text[newline_idx + 1:].strip()
                else:
                    text = text[3:].strip()
            if text.endswith("```"):
                text = text[:-3].strip()
            if "\n```" in text:
                text = text[:text.rfind("\n```")].strip()

            startIdx = text.find("{")
            endIdx = text.rfind("}")
                       
            if startIdx >= 0 and endIdx > startIdx:
                jsonStr = text[startIdx:endIdx + 1]
                print(f"DEBUG - Extracted JSON string (length {len(jsonStr)})")
                print(f"DEBUG - Attempting to parse JSON...")
                data = json.loads(jsonStr)
                print(f"DEBUG - JSON parsed successfully!")
                return data
            else:
                print(f"DEBUG - No valid JSON delimiters found (startIdx={startIdx}, endIdx={endIdx})")
                # Try to handle incomplete JSON by adding missing closing brace
                if startIdx >= 0 and endIdx == -1:
                    print("DEBUG - JSON appears incomplete, attempting to fix...")
                    jsonStr = text[startIdx:] + "}"
                    try:
                        data = json.loads(jsonStr)
                        return data
                    except json.JSONDecodeError as e:
                        print(f"DEBUG - Failed with fix: {e}")
                return {"error": "No valid JSON found in response", "raw_response": text[:200]}
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return {"error": f"Failed to parse JSON: {str(e)}", "raw_response": text[:200]}
    
    def extractInvoiceData(self, filePath: str, fileType: str = "pdf") -> Dict[str, Any]:
        """Main method to extract invoice data from uploaded file"""
        print("extracting invoice data")
        try:
            documentText = self.extractTextFromDocument(filePath, fileType)
            
            if not documentText or len(documentText.strip()) < 10:
                return {
                    "error": "Could not extract sufficient text from document.",
                    "fallback_data": self._generateFallbackData(),
                    "extracted_text_preview": ""
                }
            
            # Try Google API if available
            if self.clientAvailable:
                print("Using Google Generative AI API...")
                result = self.callLlmApi(documentText)
                
                if "error" not in result:
                    cleanedData = self._cleanExtractedData(result)
                    cleanedData["extracted_text_preview"] = documentText[:500]
                    return cleanedData
                else:
                    print(f"API failed: {result.get('error')}, using fallback...")
            
            # Fallback to rule-based extraction
            localData = self._localExtraction(documentText)
            cleanedData = self._cleanExtractedData(localData)
            cleanedData["extracted_text_preview"] = documentText[:500]
            
            return cleanedData
            
        except Exception as e:
            print(f"Error in extractInvoiceData: {e}")
            traceback.print_exc()
            return {
                "error": str(e),
                "fallback_data": self._generateFallbackData()
            }
    
    def _localExtraction(self, text: str) -> Dict[str, Any]:
        """Fallback rule-based extraction from text"""
        data = {
            "customer_name": "",
            "customer_email": "",
            "order_date": "",
            "invoice_number": f"INV-{abs(hash(text)) % 10000:04d}",
            "total_amount": 0.0,
            "tax_amount": 0.0,
            "shipping_address": "",
            "billing_address": "",
            "order_details": []
        }
        
        # Enhanced patterns for extraction
        patterns = {
            "customer_name": r'(?:customer|client|bill to|sold to|name)[:\s]*([A-Za-z\s\.]{3,50})(?:\n|$)',
            "invoice_number": r'(?:invoice|inv|number|#)[\s#:]*([A-Z0-9\-_]{3,20})',
            "total_amount": r'(?:total|amount|due|balance)[\s:$]*([\d,]+\.?\d{0,2})',
            "order_date": r'(?:date|invoice date|order date)[\s:]*([\d]{1,2}[/\-][\d]{1,2}[/\-][\d]{2,4})'
        }
        
        for field, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                if field == "total_amount":
                    try:
                        amountStr = matches[-1].replace(',', '')
                        data[field] = float(amountStr)
                    except:
                        pass
                elif field == "order_date":
                    dateStr = matches[-1].strip()
                    try:
                        for fmt in ('%m/%d/%Y', '%d/%m/%Y', '%m-%d-%Y', '%Y-%m-%d', '%d-%m-%Y'):
                            try:
                                dt = datetime.strptime(dateStr, fmt)
                                data[field] = dt.strftime('%Y-%m-%d')
                                break
                            except:
                                continue
                        if not data[field]:
                            data[field] = dateStr
                    except:
                        data[field] = dateStr
                else:
                    data[field] = matches[0].strip()
        
        return data
    
    def _cleanExtractedData(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate extracted data"""
        cleaned = {
            "customer_name": data.get("customer_name", "Unknown Customer"),
            "customer_email": data.get("customer_email", ""),
            "order_date": data.get("order_date", ""),
            "invoice_number": data.get("invoice_number", f"INV-{abs(hash(str(data))) % 10000:04d}"),
            "total_amount": float(data.get("total_amount", 0.0)),
            "tax_amount": float(data.get("tax_amount", 0.0)),
            "shipping_address": data.get("shipping_address", ""),
            "billing_address": data.get("billing_address", ""),
            "order_details": []
        }
        
        details = data.get("order_details", [])
        if isinstance(details, list):
            for detail in details:
                if isinstance(detail, dict):
                    cleanedDetail = {
                        "product_name": detail.get("product_name", "Unknown Product"),
                        "product_code": detail.get("product_code", ""),
                        "quantity": int(detail.get("quantity", 1)),
                        "unit_price": float(detail.get("unit_price", 0.0)),
                        "line_total": float(detail.get("line_total", 0.0)),
                        "description": detail.get("description", "")
                    }
                    # Calculate line_total if not provided
                    if cleanedDetail["line_total"] == 0.0:
                        cleanedDetail["line_total"] = cleanedDetail["quantity"] * cleanedDetail["unit_price"]
                    cleaned["order_details"].append(cleanedDetail)
        
        # Calculate total if not provided or incorrect
        if cleaned["total_amount"] == 0.0 and cleaned["order_details"]:
            subtotal = sum(d["line_total"] for d in cleaned["order_details"])
            cleaned["total_amount"] = subtotal + cleaned["tax_amount"]
        
        return cleaned
    
    def _generateFallbackData(self) -> Dict[str, Any]:
        """Generate sample data if LLM extraction fails"""
        invoiceNum = f"INV-FALLBACK-{random.randint(1000, 9999)}"
        orderDate = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
        
        sampleProducts = [
            {"name": "Product XYZ", "code": "23423423", "price": 150.00, "qty": 15},
            {"name": "Product ABC", "code": "45645645", "price": 75.00, "qty": 1},
            {"name": "Web Development Service", "code": "WEB-001", "price": 5000.00, "qty": 1},
            {"name": "Consulting Hours", "code": "CONS-001", "price": 150.00, "qty": 40},
        ]
        
        selectedProducts = random.sample(sampleProducts, random.randint(1, min(3, len(sampleProducts))))
        
        orderDetails = []
        subtotal = 0.0
        for product in selectedProducts:
            lineTotal = product["price"] * product["qty"]
            subtotal += lineTotal
            orderDetails.append({
                "product_name": product["name"],
                "product_code": product["code"],
                "quantity": product["qty"],
                "unit_price": product["price"],
                "line_total": lineTotal,
                "description": f"Sample {product['name']} description"
            })
        
        taxRate = 0.06875
        taxAmount = round(subtotal * taxRate, 2)
        totalAmount = subtotal + taxAmount
        
        return {
            "customer_name": "Sample Customer",
            "customer_email": "customer@example.com",
            "order_date": orderDate,
            "invoice_number": invoiceNum,
            "total_amount": round(totalAmount, 2),
            "tax_amount": taxAmount,
            "shipping_address": "123 Main St, City, State, ZIP",
            "billing_address": "123 Main St, City, State, ZIP",
            "order_details": orderDetails
        }
