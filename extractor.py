"""
extractor.py — Extracts text and images from Inspection & Thermal PDFs
Uses PyMuPDF (fitz) for reliable extraction
"""
import fitz  # PyMuPDF
import base64
from typing import Dict, List


def extract_from_pdf(pdf_path: str, doc_type: str) -> Dict:
    """
    Extract all text and images from a PDF.
    Returns structured dict with text, pages, and images.
    """
    doc = fitz.open(pdf_path)

    extracted = {
        "type": doc_type,
        "text": "",
        "pages": [],
        "images": [],
        "total_pages": len(doc),
    }

    for page_num, page in enumerate(doc):
        page_text = page.get_text()
        extracted["text"] += f"\n--- Page {page_num + 1} ---\n{page_text}"

        # Extract images from this page
        image_list = page.get_images(full=True)
        page_images = []

        for img_idx, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image.get("ext", "jpeg").lower()

                # Normalize extension
                if image_ext == "jpg":
                    image_ext = "jpeg"
                if image_ext not in ["jpeg", "png", "webp"]:
                    image_ext = "jpeg"

                image_b64 = base64.b64encode(image_bytes).decode("utf-8")

                img_info = {
                    "page": page_num + 1,
                    "index": img_idx,
                    "ext": image_ext,
                    "b64": image_b64,
                    "bytes": image_bytes,
                    "size": len(image_bytes),
                }
                page_images.append(img_info)
                extracted["images"].append(img_info)

            except Exception:
                pass  # Skip unreadable images

        extracted["pages"].append(
            {
                "page_num": page_num + 1,
                "text": page_text,
                "images": page_images,
            }
        )

    doc.close()
    return extracted


def get_key_images(images: List[Dict], max_count: int = 12) -> List[Dict]:
    """
    Select key images — one per page, capped at max_count.
    Prioritises larger images (more content).
    """
    seen_pages = set()
    selected = []

    # Sort by size descending to prefer higher-quality images
    sorted_imgs = sorted(images, key=lambda x: x["size"], reverse=True)

    for img in sorted_imgs:
        if img["page"] not in seen_pages and len(selected) < max_count:
            selected.append(img)
            seen_pages.add(img["page"])

    # Re-sort by page order for logical reading
    selected.sort(key=lambda x: x["page"])
    return selected
