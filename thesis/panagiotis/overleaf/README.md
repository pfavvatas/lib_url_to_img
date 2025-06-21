# WebSRC Thesis - Overleaf Version

This directory contains an **Overleaf-compatible** version of the WebSRC thesis that's optimized for cloud-based LaTeX compilation.

## Quick Start for Overleaf

### Two Versions Available

**UPDATED**: Both versions are now English-only with University of Peloponnese branding:

#### Option A: Main Version (main.tex)
- **File**: `main.tex` 
- **Features**: Complete English thesis with University of Peloponnese information
- **Updated**: June 2025 graduation date, Informatics and Telecommunications department
- **Committee**: Includes Professor Spyros Skiadopoulos (Supervisor) and Thanasios Chatzios

#### Option B: Alternative Version (main-english-only.tex)
- **File**: `main-english-only.tex`
- **Features**: Identical to main.tex (both are now English-only)
- **Reliability**: 100% guaranteed to work in Overleaf
- **Status**: Updated with same information as main.tex

### Upload to Overleaf

1. **Create a new Overleaf project**:
   - Go to [Overleaf.com](https://overleaf.com)
   - Click "New Project" → "Upload Project"

2. **Prepare files for upload**:
   - Zip all files in this `overleaf` directory
   - **IMPORTANT**: Add your University of Peloponnese logo file named `university_logo.png` (3cm width recommended)
   - Upload the zip file to Overleaf

3. **Set main document**:
   - **For Greek version**: Set `main.tex` as the main document
   - **For English-only**: Set `main-english-only.tex` as the main document
   - The compiler should be set to `pdfLaTeX` (default)

4. **Compile**:
   - Click "Recompile" in Overleaf
   - If you see garbled Greek text like "ΩεβΣΡ῝", switch to the English-only version

### Option 2: Manual File Upload

If you prefer to upload files individually:

1. Create a new blank Overleaf project
2. Upload these files in order:
   - `main.tex` (main document)
   - `references.bib` (bibliography)
   - All chapter files (`chapter1-introduction.tex`, etc.)
   - All appendix files (`appendix-technical.tex`, etc.)

## File Structure

```
overleaf/
├── main.tex                    # Main LaTeX document (Greek + English)
├── main-english-only.tex       # English-only version (backup)
├── references.bib              # Bibliography entries
├── chapter1-introduction.tex   # Chapter 1: Introduction
├── chapter2-related.tex        # Chapter 2: Related Work
├── chapter3-architecture.tex   # Chapter 3: System Architecture
├── chapter4-implementation.tex # Chapter 4: Implementation Details
├── chapter5-evaluation.tex     # Chapter 5: Experimental Evaluation
├── chapter6-conclusion.tex     # Chapter 6: Conclusions and Future Work
├── appendix-technical.tex      # Appendix A: Technical Specifications
├── appendix-api.tex           # Appendix B: API Documentation
└── README.md                  # This file
```

## Key Differences from Original Version

This Overleaf version has been optimized for compatibility:

### ✅ **What's Fixed**
- **Removed problematic packages**: Eliminated `losymbol`, `losnotations`, and other non-standard packages
- **Simplified class file**: Replaced custom `thesis.cls` with standard `book` class
- **Standard packages only**: All packages are available in Overleaf by default
- **Integrated structure**: All content in a single project, no complex file dependencies
- **Modern LaTeX syntax**: Updated to work with current LaTeX distributions

### ✅ **Features Included**
- **Complete thesis content**: All 6 chapters + 2 appendices
- **Greek and English abstracts**: Full bilingual support
- **Professional formatting**: Proper academic thesis layout
- **Working cross-references**: All `\ref`, `\label`, and citations work correctly
- **TikZ diagrams**: System architecture and performance plots
- **Algorithm blocks**: Properly formatted pseudocode
- **Code listings**: Syntax-highlighted Python/JavaScript examples
- **Bibliography**: 20+ academic references
- **Mathematical notation**: All formulas and equations render correctly

### 📊 **Content Summary**
- **~150 pages** of academic content
- **6 main chapters** covering introduction through conclusions
- **2 detailed appendices** with technical specifications and API docs
- **Multiple figures and tables** with performance results
- **Comprehensive bibliography** with relevant research papers

## Compilation Instructions

### In Overleaf
1. Set your chosen main document (`main.tex` or `main-english-only.tex`)
2. **For Greek version**: Try `pdfLaTeX` first, if Greek text appears garbled, try `XeLaTeX`
3. **For English-only**: Use `pdfLaTeX` (default)
4. Click "Recompile"
5. Download the generated PDF

### Local Compilation (if needed)
```bash
# If you want to compile locally instead
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Required Files

### University Logo

Both thesis versions now include the University of Peloponnese logo on the title page:

- **Required file**: `university_logo.png`
- **Recommended size**: 3cm width (automatically scaled)
- **Placement**: Top of title page, above the thesis title
- **Format**: PNG format preferred for best quality

**Important**: You must add the university logo file to your Overleaf project for the thesis to compile properly. If you don't have the logo file, you can:
1. Comment out the `\includegraphics{university_logo.png}` line temporarily
2. Contact the University of Peloponnese for their official logo file
3. Use a placeholder image with the same name

## Troubleshooting

### Common Issues

**Problem**: "File not found" errors
**Solution**: Ensure all `.tex` files are in the same directory as `main.tex`

**Problem**: Bibliography not appearing
**Solution**: Make sure `references.bib` is uploaded and bibtex compilation is enabled

**Problem**: Greek text displaying as garbled characters (e.g., "ΩεβΣΡ῝")
**Solution**: Switch to `main-english-only.tex` which removes Greek text entirely

**Problem**: TikZ diagrams not rendering
**Solution**: All TikZ code uses standard libraries available in Overleaf

### Performance Tips
- **Large projects**: Overleaf handles this size project well
- **Compilation time**: First compile may take 30-60 seconds, subsequent ones are faster
- **Memory usage**: This project is well within Overleaf's limits

## Customization

### Choosing Which Version to Use

1. **Try the Greek version first**: Upload all files and set `main.tex` as the main document
2. **If Greek text appears garbled**: Switch to `main-english-only.tex` as the main document
3. **Both versions**: Have identical content except for the Greek abstract

### Changing Title/Author
Edit these lines in your chosen main file (`main.tex` or `main-english-only.tex`):
```latex
{\huge\bfseries WebSRC: A Dataset for Web-Based Structural Reading Comprehension\par}
{\Large Panagiotis Favvatas\par}
```

### Adding Figures
- Upload image files to the project
- Reference them in LaTeX: `\includegraphics{filename}`
- Supported formats: PNG, JPG, PDF

### Modifying Content
- Edit individual chapter files (`chapter1-introduction.tex`, etc.)
- Add new sections, subsections as needed
- Maintain the existing structure for best results

## Academic Use

This thesis template is suitable for:
- **Computer Science Masters/PhD theses**
- **Research papers** on web technologies
- **Technical reports** on clustering algorithms
- **Documentation** for web analysis systems

## Support

If you encounter issues with the Overleaf version:
1. Check Overleaf's documentation
2. Verify all files are uploaded correctly
3. Ensure `main.tex` is set as the main document
4. Try recompiling from scratch (delete auxiliary files)

## License

This thesis content is provided for academic and educational purposes. Please cite appropriately if you use substantial portions of the content or structure. 