"""
Azure Document Intelligence PDF to Markdown Converter

This script demonstrates how to use Azure AI Document Intelligence with the prebuilt layout model
to convert PDF documents to Markdown format. The layout model preserves document structure
including headings, paragraphs, tables, and other formatting elements.

Features:
- Convert single PDF files to Markdown
- Process PDF documents from URLs
- Batch process multiple PDFs in a directory
- Preserve document structure and formatting
- Extract tables in Markdown table format
- Handle figures and images
- Maintain hierarchical document sections

Usage Examples:
    # Process guide.pdf or demo with sample if not found
    python docint.py
    
    # Process PDF from URL
    python docint.py url "https://example.com/document.pdf"
    
    # Process all PDFs in current directory
    python docint.py batch
    
    # Process all PDFs in specific directory
    python docint.py batch /path/to/pdfs

Requirements:
    - Azure AI Document Intelligence service
    - FOUNDRY_API_KEY environment variable set
    - azure-ai-documentintelligence package
    - python-dotenv package

Configuration:
    Set up a .env file in the workspace root with:
    FOUNDRY_API_KEY=your_document_intelligence_key
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, DocumentContentFormat


def load_environment():
    """Load environment variables from .env file"""
    # Load .env from the workspace root
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    # Get the endpoint and key from environment
    endpoint = "https://fndry-course.cognitiveservices.azure.com/"
    key = os.getenv("FOUNDRY_API_KEY")
    
    if not key:
        raise ValueError("FOUNDRY_API_KEY not found in environment variables")
    
    return endpoint, key


def create_document_intelligence_client(endpoint: str, key: str) -> DocumentIntelligenceClient:
    """Create and return a Document Intelligence client"""
    return DocumentIntelligenceClient(
        endpoint=endpoint, 
        credential=AzureKeyCredential(key)
    )


def analyze_pdf_from_file(client: DocumentIntelligenceClient, file_path: str) -> str:
    """
    Analyze a PDF file using the prebuilt layout model and return Markdown content
    
    Args:
        client: Document Intelligence client
        file_path: Path to the PDF file
        
    Returns:
        Markdown content as string
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read the PDF file
    with open(file_path, "rb") as f:
        # Begin analysis with the prebuilt layout model
        # Specify Markdown output format for clean conversion
        poller = client.begin_analyze_document(
            "prebuilt-layout",
            body=f,
            output_content_format=DocumentContentFormat.MARKDOWN
        )
    
    # Get the result
    result = poller.result()
    
    # Return the markdown content
    return result.content


def analyze_pdf_from_url(client: DocumentIntelligenceClient, url: str) -> str:
    """
    Analyze a PDF from URL using the prebuilt layout model and return Markdown content
    
    Args:
        client: Document Intelligence client
        url: URL to the PDF file
        
    Returns:
        Markdown content as string
    """
    # Begin analysis with the prebuilt layout model
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        AnalyzeDocumentRequest(url_source=url),
        output_content_format=DocumentContentFormat.MARKDOWN
    )
    
    # Get the result
    result = poller.result()
    
    # Return the markdown content
    return result.content


def save_markdown_to_file(markdown_content: str, output_path: str) -> None:
    """Save markdown content to a file"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"Markdown content saved to: {output_path}")


def main():
    """Main function to demonstrate PDF to Markdown conversion"""
    try:
        # Load environment variables
        endpoint, key = load_environment()
        print(f"Using endpoint: {endpoint}")
        
        # Create Document Intelligence client
        client = create_document_intelligence_client(endpoint, key)
        print("Document Intelligence client created successfully")
        
        # Path to the PDF file
        pdf_path = Path(__file__).parent / "guide.pdf"
        
        if pdf_path.exists():
            print(f"Analyzing PDF: {pdf_path}")
            
            # Analyze the PDF and convert to Markdown
            markdown_content = analyze_pdf_from_file(client, str(pdf_path))
            
            # Save the markdown to a file
            output_path = pdf_path.with_suffix(".md")
            save_markdown_to_file(markdown_content, str(output_path))
            
            # Print statistics
            lines = markdown_content.split('\n')
            print(f"\n--- Document Analysis Complete ---")
            print(f"Original PDF: {pdf_path.name}")
            print(f"Output file: {output_path.name}")
            print(f"Total lines: {len(lines)}")
            print(f"Total characters: {len(markdown_content)}")
            
            # Print first 500 characters as preview
            print("\n--- Markdown Preview ---")
            print(markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content)
            
        else:
            print(f"PDF file not found at: {pdf_path}")
            
            # Demo with a sample URL instead
            sample_url = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-layout.pdf"
            print(f"Analyzing sample PDF from URL: {sample_url}")
            
            markdown_content = analyze_pdf_from_url(client, sample_url)
            
            # Save the sample markdown
            output_path = Path(__file__).parent / "sample_layout.md"
            save_markdown_to_file(markdown_content, str(output_path))
            
            # Print statistics
            lines = markdown_content.split('\n')
            print(f"\n--- Document Analysis Complete ---")
            print(f"Source URL: {sample_url}")
            print(f"Output file: {output_path.name}")
            print(f"Total lines: {len(lines)}")
            print(f"Total characters: {len(markdown_content)}")
            
            # Print preview
            print("\n--- Markdown Preview ---")
            print(markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content)
        
    except Exception as e:
        print(f"Error: {e}")


def analyze_multiple_files(directory_path: str | None = None):
    """
    Analyze multiple PDF files in a directory
    
    Args:
        directory_path: Path to directory containing PDF files
    """
    if directory_path is None:
        dir_path = Path(__file__).parent
    else:
        dir_path = Path(directory_path)
    
    try:
        # Load environment and create client
        endpoint, key = load_environment()
        client = create_document_intelligence_client(endpoint, key)
        
        # Find all PDF files in the directory
        pdf_files = list(dir_path.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {dir_path}")
            return
        
        print(f"Found {len(pdf_files)} PDF files to process:")
        
        for pdf_file in pdf_files:
            print(f"\nProcessing: {pdf_file.name}")
            try:
                # Analyze the PDF
                markdown_content = analyze_pdf_from_file(client, str(pdf_file))
                
                # Save markdown file
                output_path = pdf_file.with_suffix(".md")
                save_markdown_to_file(markdown_content, str(output_path))
                
                print(f"✓ Successfully converted {pdf_file.name} to {output_path.name}")
                
            except Exception as e:
                print(f"✗ Failed to process {pdf_file.name}: {e}")
                
    except Exception as e:
        print(f"Error in batch processing: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "batch":
            # Batch processing mode
            directory = sys.argv[2] if len(sys.argv) > 2 else None
            analyze_multiple_files(directory)
        elif sys.argv[1] == "url":
            # URL processing mode
            if len(sys.argv) < 3:
                print("Usage: python docint.py url <pdf_url>")
                sys.exit(1)
            url = sys.argv[2]
            try:
                endpoint, key = load_environment()
                client = create_document_intelligence_client(endpoint, key)
                markdown_content = analyze_pdf_from_url(client, url)
                
                # Save with filename based on URL
                import urllib.parse
                parsed_url = urllib.parse.urlparse(url)
                filename = Path(parsed_url.path).stem or "document"
                output_path = Path(__file__).parent / f"{filename}.md"
                save_markdown_to_file(markdown_content, str(output_path))
                
                print(f"Successfully converted URL to {output_path.name}")
            except Exception as e:
                print(f"Error processing URL: {e}")
        else:
            print("Usage:")
            print("  python docint.py           # Process guide.pdf or demo with sample")
            print("  python docint.py batch     # Process all PDFs in current directory")
            print("  python docint.py batch <dir>  # Process all PDFs in specified directory")
            print("  python docint.py url <url>    # Process PDF from URL")
    else:
        # Default mode
        main()
