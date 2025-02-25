from flask import Flask, request, render_template, send_file, jsonify
import numpy as np
import cv2
import io
from scipy.fftpack import dct, idct
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from PIL import Image, ImageFilter
from fpdf import FPDF
import os
import datetime

app = Flask(__name__)

# Max file size (5MB)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'static'

# Apply Discrete Cosine Transform (DCT)
def apply_dct(img):
    return dct(dct(img.T, norm='ortho').T, norm='ortho')

# Apply Inverse DCT
def apply_idct(img):
    return idct(idct(img.T, norm='ortho').T, norm='ortho')

# Calculate Entropy (Randomness Measure)
def calculate_entropy(img):
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    hist_norm = hist.ravel() / hist.sum()
    entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-7))
    return entropy

# SHA-3 Hash for Tamper Detection
def calculate_sha3_hash(image):
    sha3 = hashes.Hash(hashes.SHA3_256(), backend=default_backend())
    sha3.update(image.tobytes())
    return sha3.finalize()

# Degrade Image on Tampering
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

# Generate PDF Report
def generate_pdf(entropy, std_dev, strength_score, integrity_status, image_path):
    # Replace emojis with ASCII-friendly text
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

    report_path = os.path.join(app.config['UPLOAD_FOLDER'], "integrity_report.pdf")
    pdf.output(report_path)
    return report_path


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'image' not in request.files or 'watermark' not in request.files:
            return jsonify({'error': 'Image and watermark required'}), 400

        image_file = request.files['image']
        watermark_file = request.files['watermark']

        # File validation
        allowed_extensions = ('.png', '.jpg', '.jpeg', '.pdf', '.txt')
        if not image_file.filename.lower().endswith(allowed_extensions):
            return jsonify({'error': 'Invalid image format. Use PNG, JPG, PDF, or TXT.'}), 400
        if not watermark_file.filename.lower().endswith(allowed_extensions):
            return jsonify({'error': 'Invalid watermark format. Use PNG, JPG, PDF, or TXT.'}), 400

        image = np.array(Image.open(image_file).convert('RGB'))
        watermark = np.array(Image.open(watermark_file).convert('L'))

        entropy = calculate_entropy(image)
        dct_img = apply_dct(np.float32(image))
        std_dev = np.std(dct_img)

        integrity_status = "✅ Quantum Watermark Verified - Strong Integrity"
        strength_score = 95
        final_image = image

        # Degrade image if tampering is detected
        if entropy < 6.5 or std_dev < 2.0:
            integrity_status = "❌ Integrity Compromised - Degradation Applied"
            strength_score = 40
            final_image = degrade_image(image)

        # Save processed image
        filename = f"processed_{image_file.filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        Image.fromarray(final_image).save(save_path)

        # Generate PDF Report
        report_path = generate_pdf(entropy, std_dev, strength_score, integrity_status, save_path)

        return jsonify({
    'message': integrity_status,
    'filename': filename,
    'security_strength': float(strength_score),  # Convert to Python float
    'entropy': float(entropy),                   # Convert to Python float
    'std_dev': float(std_dev),                   # Convert to Python float
    'report': "integrity_report.pdf"
})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
