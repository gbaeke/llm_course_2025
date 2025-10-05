# Azure Document Intelligence PDF to Markdown Converter

This script demonstrates how to use Azure AI Document Intelligence with the prebuilt layout model to convert PDF documents to Markdown format.

## Features

- ✅ Convert single PDF files to Markdown
- ✅ Process PDF documents from URLs
- ✅ Batch process multiple PDFs in a directory
- ✅ Preserve document structure and formatting
- ✅ Extract tables in Markdown table format
- ✅ Handle figures and document sections
- ✅ Maintain hierarchical document structure

## Setup

1. Ensure you have Azure Document Intelligence service set up
2. Set the `FOUNDRY_API_KEY` environment variable in `.env` file
3. Install required packages:
   ```bash
   pip install azure-ai-documentintelligence python-dotenv
   ```

## Usage

### Process a single PDF file
```bash
python docint.py
```
This will process `guide.pdf` if it exists, or demo with a sample PDF from URL.

### Process PDF from URL
```bash
python docint.py url "https://example.com/document.pdf"
```

### Batch process PDFs in current directory
```bash
python docint.py batch
```

### Batch process PDFs in specific directory
```bash
python docint.py batch /path/to/pdfs
```

## Configuration

The script uses the following configuration:
- **Endpoint**: `https://fndry-course.cognitiveservices.azure.com/`
- **API Key**: Loaded from `FOUNDRY_API_KEY` environment variable in `.env` file
- **Model**: `prebuilt-layout` (Azure's layout analysis model)
- **Output Format**: `markdown` (structured Markdown output)

## Example Output

The script converts PDFs to clean Markdown format that preserves:
- Document headers and structure
- Tables with proper Markdown table syntax
- Page breaks and sections
- Hierarchical headings
- Figure placeholders

Sample output:
```markdown
# Document Title

## Section 1

This is the content of section 1.

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |

## Section 2

More content here...
```

## Benefits of the Layout Model

1. **Simplified processing**: Parse different document types (PDF, images, Office files) with a single API call
2. **Scalability and AI quality**: High-quality OCR and structure analysis supporting 309 printed and 12 handwritten languages
3. **LLM compatibility**: Markdown output is optimized for large language model consumption and RAG applications

## Error Handling

The script includes comprehensive error handling for:
- Missing environment variables
- Invalid file paths or URLs
- Network connectivity issues
- Document Intelligence service errors
- File I/O operations