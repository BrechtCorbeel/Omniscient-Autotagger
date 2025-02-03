<!-- Badges -->
![Windows](https://img.shields.io/badge/Windows%2010,%2011-%230079d5.svg?style=for-the-badge&logo=Windows%2011&logoColor=white)
![Linux (AppImage)](https://img.shields.io/badge/Linux%20(AppImage)-FCC624?style=for-the-badge&logo=linux&logoColor=black)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/BrechtCorbeel/Omniscient-Autotagger/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Version](https://img.shields.io/github/v/release/BrechtCorbeel/Omniscient-Autotagger)](https://github.com/BrechtCorbeel/Omniscient-Autotagger/releases)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)

<div align="center">
  <img src="https://github.com/user-attachments/assets/0502a84f-f4a8-4be6-9e22-7cfd364d18a2" alt="Omniscient Autotagger Banner" style="max-width:100%;">
</div>

---

## Overview

Omniscient Autotagger is a powerful, intelligent tool designed to automatically tag your files with precision. This project combines cutting-edge algorithms with a user-friendly interface to streamline the tagging process for various file types.  
This repository is an ongoing project.  
Current implementation works on Linux and Windows.

---

## Quick Navigation

<p align="center">
  <a href="#overview" style="text-decoration:none;">
    <button style="background-color:#444; color:#fff; border: none; padding: 10px 20px; margin: 5px; cursor: pointer;">Overview</button>
  </a>
  <a href="#features" style="text-decoration:none;">
    <button style="background-color:#444; color:#fff; border: none; padding: 10px 20px; margin: 5px; cursor: pointer;">Features</button>
  </a>
  <a href="#installation" style="text-decoration:none;">
    <button style="background-color:#444; color:#fff; border: none; padding: 10px 20px; margin: 5px; cursor: pointer;">Installation</button>
  </a>
  <a href="#usage" style="text-decoration:none;">
    <button style="background-color:#444; color:#fff; border: none; padding: 10px 20px; margin: 5px; cursor: pointer;">Usage</button>
  </a>
  <a href="#configuration" style="text-decoration:none;">
    <button style="background-color:#444; color:#fff; border: none; padding: 10px 20px; margin: 5px; cursor: pointer;">Configuration</button>
  </a>
  <a href="#to-do" style="text-decoration:none;">
    <button style="background-color:#444; color:#fff; border: none; padding: 10px 20px; margin: 5px; cursor: pointer;">TO DO</button>
  </a>
  <a href="#contributing" style="text-decoration:none;">
    <button style="background-color:#444; color:#fff; border: none; padding: 10px 20px; margin: 5px; cursor: pointer;">Contributing</button>
  </a>
  <a href="#license" style="text-decoration:none;">
    <button style="background-color:#444; color:#fff; border: none; padding: 10px 20px; margin: 5px; cursor: pointer;">License</button>
  </a>
</p>

---

## Features

- **Automatic Tagging:** Intelligent algorithms that tag files quickly and accurately.
- **Cross-Platform Compatibility:** Currently implemented for Linux and Windows.
- **Customizable Workflow:** Easily integrate with your existing file management systems.
- **Optimized Performance:** Uses proper multithreading for smooth and responsive operation.
- **User-Friendly Interface:** Built with PyQt6, featuring a sleek dark grey aesthetic.
- **Persistent Settings:** Saves configuration data in an OS-specific folder (AppData on Windows or the equivalent on Linux) to reload your preferences upon launch.

---

## Installation

Clone the repository and install the required packages:

```bash
git clone https://github.com/BrechtCorbeel/Omniscient-Autotagger.git
cd Omniscient-Autotagger
pip install -r requirements.txt
```
Note: For full GUI functionality, ensure that PyQt6 is installed.

## Usage
Run the main application using:

bash
Copy
python main.py
The application will automatically create a folder in your OS's application data directory (e.g., AppData on Windows or the corresponding location on Linux) to store and reload GUI settings and user preferences.

## Configuration
Customize the autotagging parameters by editing the configuration file located in the application data folder. This file allows you to adjust settings to better match your workflow and performance requirements.

## TO DO
Expand and enhance settings.
Drag-and-drop window frame image file.
Support basic Windows frame scaling.
Add tracking features.
Proper threading and implementation for tracking progress.
Cloud features.
Large + lite version.
Paid features.
Image tags.
Basic drawing and editing features.
Video tagging.
...


## Contributing
Contributions are welcome! Follow these steps to contribute:

Fork the repository.
Create a new branch:
git checkout -b feature/YourFeature
Commit your changes:
git commit -m 'Add some feature'
Push to the branch:
git push origin feature/YourFeature
Open a pull request.
For any major changes, please open an issue first to discuss what you would like to modify.


<div align="center"> <a href="https://github.com/BrechtCorbeel/Omniscient-Autotagger" style="text-decoration:none;"> <button style="background-color:#444; color:#fff; border: none; padding: 10px 20px; margin: 5px; cursor: pointer;">View on GitHub</button> </a> <a href="https://github.com/BrechtCorbeel" style="text-decoration:none;"> <button style="background-color:#444; color:#fff; border: none; padding: 10px 20px; margin: 5px; cursor: pointer;">More Projects</button> </a> </div> ```
