# TikTokDL

## Description

This is a simple application I made in python which can automatically download likes and favorites from exported tiktok JSON data. 

TikTokDL will try and download as fast as possible and should really only be limited by your internet, as of now there can be an error rate of 20-50% but this may be improved in the future. Multiple passes may result in more TikToks fully processed and downloaded.

## Requirements

- Python 3.10 or newer (could work with older versions, haven't tested)

Install these two libraries for the program to function

- Pyktok
- Termcolor

## How To Use

1. Export all data or just activity from TikTok in JSON format, you can google how to do this.

2. Download the data and extract the "user_data_tiktok.json" file and insert it into the TikTokDL folder.

3. Run the program and it should go through and download as many likes and favorites that it can.
