# 🎉 DouyinEmojiAPI - Access Fun Douyin Emojis Easily

[![Download DouyinEmojiAPI](https://img.shields.io/badge/Download-DouyinEmojiAPI-brightgreen)](https://github.com/Ducdeptraihhh/DouyinEmojiAPI/releases)

## 🚀 Getting Started

Welcome to DouyinEmojiAPI! This tool allows you to work with Douyin emojis easily. Follow these simple steps to download and run this application.

## 📥 Download & Install

1. Visit the [Releases page](https://github.com/Ducdeptraihhh/DouyinEmojiAPI/releases) to download the latest version of DouyinEmojiAPI.
   
2. Choose the package suitable for your operating system and download it.

## ⚙️ Installation Steps

To install DouyinEmojiAPI, you need to have Python installed on your computer. If you haven’t installed Python, please download it from the [official website](https://www.python.org/downloads/).

1. Open your terminal or command prompt.
  
2. Change to the directory where you downloaded the package.

3. Run this command to install required libraries:

   ```bash
   pip install -r requirements.txt
   ```

## 📂 Configuration

To use the API, you need to create a configuration file with your settings.

1. Copy the configuration template with this command:

   ```bash
   cp config.example.py config.py
   ```

2. Open `config.py` and fill in the details:

   - **cookie:** Enter your Douyin cookie.
   - **base_url:** Enter your IP address.
   - **allowed_wxids:** Enter a list of wxids you wish to permit.

## 🚀 Starting the Server

Once installed and configured, you can start the server.

1. Use the following command:

   ```bash
   python3 server.py
   ```

2. The server will start at `http://your_IP:8000`. Make sure to replace `your_IP` with your actual IP address.

## 🎨 Douyin Assistant Configuration

In the Douyin Assistant application, you need to set a custom API.

1. Go to the custom API section in Douyin Assistant.

2. Input the following URL:

   ```
   http://your_IP:8000/emoticon_api
   ```

Replace `your_IP` with your server's IP address.

## ❓ Frequently Asked Questions

### **Q: What if the download fails?**
A: Check if your cookie is expired. Try updating the cookie.  
B: If the issue persists, there may be a bug.

### **Q: What if the conversion fails?**
A: Ensure all required libraries are installed. Check that your image format is supported.  
B: If problems continue, that may hint at a bug.

### **Q: What if I cannot fetch paginated data?**
A: This is a limitation of the Douyin API. Typically, it only retrieves a few pages of data.  
B: If you experience further issues, it might be a bug.

### **Q: What if I have other questions?**
A: That’s common, as I am still learning. Remember, this is just the first version.

### **License**

DouyinEmojiAPI is open-source and free to use under the MIT License. You may explore the code and contribute if you wish.

## 👥 Community Support

If you encounter problems or need help, feel free to ask in the Issues section of the repository. Your feedback helps improve the application.

For more detailed documentation, please refer to the official [Douyin Emoji API documentation](https://mp.weixin.qq.com/s/5fisJvX-JzF6dW6UOF3amA). 

## 📧 Contact

For further inquiries, you can reach me through the GitHub repository. I appreciate your interest in DouyinEmojiAPI. Your support makes a difference.

---

This tool is for research purposes only. Users assume all risks associated with its use.