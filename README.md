# Quranic Verse Fetcher

## Notice: This Project was made with the help of Artificial Intelligence.

A Python command-line tool to fetch Quranic verses from AlQuran.cloud API using chapter:verse format input.

## Features

- Fetch verses using simple `chapter:verse` format (e.g., `2:255`)
- Support for multiple English translations
- Input validation for chapter (1-114) and verse numbers
- Multiple output formats (Arabic only, translation only, or both)
- Save results to file
- Comprehensive error handling
- Network timeout and retry logic
- Clean, readable output formatting

## Installation

No additional packages required beyond Python's standard library. The script uses:
- `requests` - for HTTP API calls
- `argparse` - for command-line interface
- `json` - for API response parsing
- `re` - for input validation

## Usage
