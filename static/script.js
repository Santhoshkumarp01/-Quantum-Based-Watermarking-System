document.getElementById('processButton').addEventListener('click', async () => {
    const mainImage = document.getElementById('mainImage').files[0];
    const watermarkImage = document.getElementById('watermarkImage').files[0];
  
    if (!mainImage || !watermarkImage) {
      alert('Please upload both main image and watermark!');
      return;
    }
  
    const formData = new FormData();
    formData.append('image', mainImage);
    formData.append('watermark', watermarkImage);
  
    try {
      const response = await fetch('/upload', { method: 'POST', body: formData });
      const data = await response.json();
      const resultUrl = data.result;
  
      document.getElementById('resultImage').src = resultUrl;
      document.getElementById('downloadButton').href = resultUrl;
      document.querySelector('.result-section').classList.remove('hidden');
    } catch (error) {
      console.error('Error processing watermark:', error);
    }
  });
  