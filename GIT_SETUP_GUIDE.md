# Git Setup Guide for Windows

You need to install Git first before we can migrate to GitHub. Here's how:

## 🔧 **Step 1: Install Git**

### **Option A: Download Git for Windows (Recommended)**
1. Go to: https://git-scm.com/download/win
2. Download the latest version (should auto-detect 64-bit)
3. Run the installer
4. **Important installer settings:**
   - ✅ Use Git from the command line and also from 3rd-party software
   - ✅ Use the OpenSSL library
   - ✅ Checkout Windows-style, commit Unix-style line endings
   - ✅ Use Windows' default console window
   - ✅ Default (fast-forward or merge)
   - ✅ Git Credential Manager
   - ✅ Enable file system caching
   - ✅ Enable symbolic links

### **Option B: Install via Winget (if you have it)**
```cmd
winget install --id Git.Git -e --source winget
```

### **Option C: Install via Chocolatey (if you have it)**
```cmd
choco install git
```

## 🔧 **Step 2: Verify Installation**
After installation, **close and reopen your terminal**, then run:
```bash
git --version
```

You should see something like: `git version 2.43.0.windows.1`

## 🔧 **Step 3: Configure Git**
Set up your identity (use your GitHub username and email):
```bash
git config --global user.name "Your GitHub Username"
git config --global user.email "your.email@example.com"
```

## 🔧 **Step 4: Initialize Your Repository**
In your VibeBot directory, run:
```bash
git init
```

## 🔧 **Step 5: Connect to GitHub**
If you already have a GitHub repository:
```bash
git remote add origin https://github.com/yourusername/your-repo-name.git
```

If you need to create a new repository:
1. Go to GitHub.com
2. Click "New repository"
3. Name it "VibeBot" (or whatever you prefer)
4. Don't initialize with README (we already have files)
5. Copy the repository URL
6. Run: `git remote add origin [your-repo-url]`

## 🚀 **After Git is Installed**

Once Git is working, we'll continue with the migration:

1. **Add all new files:**
   ```bash
   git add .
   ```

2. **Make initial commit:**
   ```bash
   git commit -m "feat: Add modular SOLID architecture with card game system"
   ```

3. **Push to GitHub:**
   ```bash
   git push -u origin main
   ```

## 📝 **What to Do Right Now**

1. **Install Git** using Option A above (download from git-scm.com)
2. **Close and reopen your terminal** after installation
3. **Tell me when it's done** and I'll guide you through the next steps!

---

**Don't worry - this is a one-time setup and then everything will be smooth sailing! 🚀**
