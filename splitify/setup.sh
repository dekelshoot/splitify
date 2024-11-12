# Update the package list
echo "Updating package list..."
sudo apt update

# Install FFmpeg
echo "Installing FFmpeg..."
sudo apt install -y ffmpeg

echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt