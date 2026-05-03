import fitz  # pymupdf
import os

def pdf_to_images(pdf_paths, doctor_id, output_dir):
    """
    Converts a list of PDF paths into PNG images.
    Returns a list of dictionaries grouping images by document.
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for pdf_path in pdf_paths:
        doc_name = os.path.basename(pdf_path).replace(".pdf", "")
        print(f"  [pdf_to_images] Converting {doc_name}.pdf ...")
        
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"  [pdf_to_images] Failed to open {pdf_path}: {e}")
            continue
            
        paths = []
        for i, page in enumerate(doc):
            # 200 DPI
            mat = fitz.Matrix(200 / 72, 200 / 72)
            pix = page.get_pixmap(matrix=mat)
            
            out_path = os.path.join(output_dir, f"{doc_name}_page_{i}.png")
            pix.save(out_path)
            paths.append(out_path)
            
        results.append({
            "doc_name": doc_name,
            "pages": paths
        })
        
    return results
