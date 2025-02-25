import cv2
import numpy as np
from scipy.fftpack import dct
from PIL import Image, ImageFilter
from fpdf import FPDF
import os
import datetime

# 📊 Apply Discrete Cosine Transform (DCT)
def apply_dct(img):
    return dct(dct(img.T, norm='ortho').T, norm='ortho')

# 📊 Calculate Entropy (Randomness Measure)
def calculate_entropy(img):
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    hist_norm = hist.ravel() / hist.sum()
    entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-7))
    return entropy

# 🛡️ Degrade Image if Tampered
def degrade_image(image):
    pil_image = Image.fromarray(image)
    blurred = pil_image.filter(ImageFilter.GaussianBlur(radius=5))
    degraded = np.array(blurred)

    # Add Noise
    noise = np.random.randint(0, 50, degraded.shape, dtype='uint8')
    degraded = cv2.add(degraded, noise)

    # Reduce Resolution
    scale_percent = 70
    width = int(degraded.shape[1] * scale_percent / 100)
    height = int(degraded.shape[0] * scale_percent / 100)
    degraded = cv2.resize(degraded, (width, height), interpolation=cv2.INTER_LINEAR)
    degraded = cv2.resize(degraded, (pil_image.width, pil_image.height), interpolation=cv2.INTER_LINEAR)

    return degraded

def generate_pdf(entropy, std_dev, strength_score, integrity_status, image_path):
    # Replace emojis with ASCII-compatible text
    integrity_status_clean = integrity_status.replace("✅", "Verified").replace("❌", "Compromised")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Quantum Integrity Check Report", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(200, 10, f"Entropy Level: {entropy:.2f}", ln=True)
    pdf.cell(200, 10, f"DCT Std Deviation: {std_dev:.2f}", ln=True)
    pdf.cell(200, 10, f"Security Strength: {strength_score}%", ln=True)
    pdf.cell(200, 10, f"Integrity Status: {integrity_status_clean}", ln=True)
    pdf.image(image_path, x=10, y=80, w=180)

    report_path = os.path.join("integrity_report.pdf")
    pdf.output(report_path)
    print(f"📄 PDF report generated at: {report_path}")

def quantum_integrity_check(image_path):
    try:
        # Load and preprocess the image
        image = np.array(Image.open(image_path).convert('RGB'))
        grayscale_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Calculate entropy & DCT
        entropy = calculate_entropy(grayscale_image)
        dct_img = apply_dct(np.float32(grayscale_image))
        std_dev = np.std(dct_img)

        # Determine integrity status
        integrity_status = "✅ Verified"
        strength_score = 95

        if entropy < 6.5 or std_dev < 2.0:
            integrity_status = "❌ Integrity Compromised - Degradation Applied"
            strength_score = 40
            image = degrade_image(image)

        # Save the (possibly degraded) image
        processed_image_path = "processed_image.png"
        Image.fromarray(image).save(processed_image_path)

        # Generate PDF Report
        generate_pdf(entropy, std_dev, strength_score, integrity_status, processed_image_path)

        # Show Results
        print("\n🔍 Quantum Integrity Check Results")
        print("-----------------------------------")
        print(f"📊 Entropy Level       : {entropy:.2f}")
        print(f"📊 DCT Std Deviation   : {std_dev:.2f}")
        print(f"🔒 Security Strength   : {strength_score}%")
        print(f"🛡️ Integrity Status    : {integrity_status}")
        print("-----------------------------------")
        print(f"📁 Processed Image Saved as: {processed_image_path}")

    except Exception as e:
        print(f"❌ Error during integrity check: {e}")

# 🚀 Example Usage
if __name__ == "__main__":
    # Change the path to your image file for testing
    quantum_integrity_check(r"C:\Users\Santhosh kumar P\Downloads\processed_certificate (1).jpg")
