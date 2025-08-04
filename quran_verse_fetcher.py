#!/usr/bin/env python3
"""
Quranic Verse Fetcher
A command-line tool to fetch Quranic verses from AlQuran.cloud API
Supports chapter:verse format input (e.g., 3:10)
"""

import argparse
import json
import re
import sys
import os
from typing import Dict, Optional, Tuple, List
import requests
from urllib.parse import quote


class QuranAPI:
    """Interface for interacting with AlQuran.cloud API"""
    
    BASE_URL = "http://api.alquran.cloud/v1"
    
    # Popular translation editions
    TRANSLATIONS = {
        'sahih': 'en.sahih',           # Sahih International
        'pickthall': 'en.pickthall',   # Pickthall
        'yusufali': 'en.yusufali',     # Yusuf Ali
        'asad': 'en.asad',             # Muhammad Asad
        'hilali': 'en.hilali',         # Hilali & Khan
        'shakir': 'en.shakir',         # Shakir
        'wahiduddin': 'en.wahiduddin', # Wahiduddin Khan
        'clearquran': 'en.clearquran', # Clear Quran
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.timeout = 10
    
    def get_verse(self, chapter: int, verse: int, translation: Optional[str] = None) -> Dict:
        """
        Fetch a specific verse from the API
        
        Args:
            chapter: Chapter number (1-114)
            verse: Verse number
            translation: Translation edition (optional)
        
        Returns:
            Dictionary containing verse data
        
        Raises:
            requests.RequestException: For network-related errors
            ValueError: For invalid responses
        """
        verse_key = f"{chapter}:{verse}"
        
        # Get Arabic text
        arabic_url = f"{self.BASE_URL}/ayah/{verse_key}"
        
        try:
            arabic_response = self._make_request(arabic_url)
            arabic_data = arabic_response.json()
            
            if arabic_data.get('code') != 200:
                raise ValueError(f"API Error: {arabic_data.get('status', 'Unknown error')}")
            
            result = {
                'verse_key': verse_key,
                'arabic': arabic_data['data'],
                'translation': None
            }
            
            # Get translation if requested
            if translation:
                trans_edition = self.TRANSLATIONS.get(translation, translation)
                trans_url = f"{self.BASE_URL}/ayah/{verse_key}/{trans_edition}"
                
                try:
                    trans_response = self._make_request(trans_url)
                    trans_data = trans_response.json()
                    
                    if trans_data.get('code') == 200:
                        result['translation'] = trans_data['data']
                    else:
                        print(f"Warning: Could not fetch translation '{translation}'. Using Arabic only.", file=sys.stderr)
                except requests.RequestException as e:
                    print(f"Warning: Translation request failed: {e}", file=sys.stderr)
            
            return result
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Network error while fetching verse: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from API: {e}")
    
    def _make_request(self, url: str) -> requests.Response:
        """Make HTTP request with proper error handling"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.Timeout:
            raise requests.RequestException("Request timed out. Please check your internet connection.")
        except requests.ConnectionError:
            raise requests.RequestException("Connection error. Please check your internet connection.")
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                raise requests.RequestException("Verse not found. Please check chapter and verse numbers.")
            elif e.response.status_code == 429:
                raise requests.RequestException("Too many requests. Please wait a moment and try again.")
            else:
                raise requests.RequestException(f"HTTP error {e.response.status_code}: {e}")
    
    def get_available_translations(self) -> List[str]:
        """Get list of available translation keys"""
        return list(self.TRANSLATIONS.keys())


class InputValidator:
    """Validates user input for chapter:verse format"""
    
    # Total verses in each chapter (1-114)
    CHAPTER_VERSES = {
        1: 7, 2: 286, 3: 200, 4: 176, 5: 120, 6: 165, 7: 206, 8: 75, 9: 129, 10: 109,
        11: 123, 12: 111, 13: 43, 14: 52, 15: 99, 16: 128, 17: 111, 18: 110, 19: 98, 20: 135,
        21: 112, 22: 78, 23: 118, 24: 64, 25: 77, 26: 227, 27: 93, 28: 88, 29: 69, 30: 60,
        31: 34, 32: 30, 33: 73, 34: 54, 35: 45, 36: 83, 37: 182, 38: 88, 39: 75, 40: 85,
        41: 54, 42: 53, 43: 89, 44: 59, 45: 37, 46: 35, 47: 38, 48: 29, 49: 18, 50: 45,
        51: 60, 52: 49, 53: 62, 54: 55, 55: 78, 56: 96, 57: 29, 58: 22, 59: 24, 60: 13,
        61: 14, 62: 11, 63: 11, 64: 18, 65: 12, 66: 12, 67: 30, 68: 52, 69: 52, 70: 44,
        71: 28, 72: 28, 73: 20, 74: 56, 75: 40, 76: 31, 77: 50, 78: 40, 79: 46, 80: 42,
        81: 29, 82: 19, 83: 36, 84: 25, 85: 22, 86: 17, 87: 19, 88: 26, 89: 30, 90: 20,
        91: 15, 92: 21, 93: 11, 94: 8, 95: 8, 96: 19, 97: 5, 98: 8, 99: 8, 100: 11,
        101: 11, 102: 8, 103: 3, 104: 9, 105: 5, 106: 4, 107: 7, 108: 3, 109: 6, 110: 3,
        111: 5, 112: 4, 113: 5, 114: 6
    }
    
    @staticmethod
    def validate_input(user_input: str) -> Tuple[int, int]:
        """
        Validate and parse chapter:verse input
        
        Args:
            user_input: String in format "chapter:verse"
        
        Returns:
            Tuple of (chapter, verse) numbers
        
        Raises:
            ValueError: For invalid input format or numbers
        """
        if not user_input or not isinstance(user_input, str):
            raise ValueError("Input cannot be empty")
        
        # Check format using regex
        pattern = r'^(\d+):(\d+)$'
        match = re.match(pattern, user_input.strip())
        
        if not match:
            raise ValueError(
                "Invalid format. Please use 'chapter:verse' format (e.g., '2:255', '3:10')"
            )
        
        chapter, verse = int(match.group(1)), int(match.group(2))
        
        # Validate chapter number (1-114)
        if chapter < 1 or chapter > 114:
            raise ValueError(f"Chapter number must be between 1 and 114. Got: {chapter}")
        
        # Validate verse number for the specific chapter
        max_verses = InputValidator.CHAPTER_VERSES.get(chapter)
        if not max_verses:
            raise ValueError(f"Unknown chapter: {chapter}")
        
        if verse < 1 or verse > max_verses:
            raise ValueError(
                f"Chapter {chapter} has {max_verses} verses. "
                f"Verse number must be between 1 and {max_verses}. Got: {verse}"
            )
        
        return chapter, verse


class OutputFormatter:
    """Formats and displays verse data"""
    
    @staticmethod
    def format_verse(verse_data: Dict, output_format: str = 'both') -> str:
        """
        Format verse data for display
        
        Args:
            verse_data: Dictionary containing verse information
            output_format: 'arabic', 'translation', or 'both'
        
        Returns:
            Formatted string for display
        """
        lines = []
        arabic = verse_data.get('arabic', {})
        translation = verse_data.get('translation')
        
        # Header with verse reference
        verse_key = verse_data.get('verse_key', 'Unknown')
        surah_name = arabic.get('surah', {}).get('englishName', 'Unknown')
        surah_arabic = arabic.get('surah', {}).get('name', '')
        
        lines.append("=" * 60)
        # Format Arabic surah name properly
        formatted_surah_arabic = f"\u200F{surah_arabic}" if surah_arabic else ""
        lines.append(f"Verse: {verse_key} | Surah: {surah_name} ({formatted_surah_arabic})")
        lines.append("=" * 60)
        
        # Arabic text
        if output_format in ['arabic', 'both'] and arabic:
            lines.append("\n Arabic Text:")
            arabic_text = arabic.get('text', 'No Arabic text available')
            # Add RTL mark for proper Arabic display
            formatted_arabic = f"\u200F{arabic_text}"
            lines.append(formatted_arabic)
            
            # Additional Arabic info
            if arabic.get('numberInSurah'):
                lines.append(f"   └─ Verse {arabic['numberInSurah']} in Surah")
        
        # Translation
        if output_format in ['translation', 'both'] and translation:
            lines.append("\n English Translation:")
            lines.append(translation.get('text', 'No translation available'))
            
            # Translation info
            edition_name = translation.get('edition', {}).get('englishName', 'Unknown')
            lines.append(f"   └─ Translation: {edition_name}")
        
        # Verse location info
        if arabic:
            juz = arabic.get('juz')
            page = arabic.get('page')
            if juz or page:
                lines.append("\n Location:")
                if juz:
                    lines.append(f"   └─ Juz (Para): {juz}")
                if page:
                    lines.append(f"   └─ Page: {page}")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
    
    @staticmethod
    def save_to_file(content: str, filename: str) -> bool:
        """
        Save formatted content to file
        
        Args:
            content: Text content to save
            filename: Output filename
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except IOError as e:
            print(f"Error saving to file '{filename}': {e}", file=sys.stderr)
            return False

def run_interactive_mode():
    """Run the application in interactive mode"""
    print("=" * 60)
    print("Quran Verse Fetcher")
    print("=" * 60)
    print()
    
    api = QuranAPI()
    
    while True:
        try:
            print("Enter a verse in format 'chapter:verse' (e.g., '2:255', '1:1')")
            print("Or type 'list' to see available translations, 'help' for examples, or 'quit' to exit.")
            
            user_input = input("\n Verse: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n Thank you for using Quran Verse Fetcher! May Allah bless you.")
                break
            elif user_input.lower() == 'list':
                translations = api.get_available_translations()
                print("\n Available translations:")
                for trans in translations:
                    print(f"  - {trans}")
                print()
                continue
            elif user_input.lower() == 'help':
                print("\n Examples:")
                print("  2:255     - Ayat al-Kursi")
                print("  1:1       - Al-Fatiha, verse 1")
                print("  3:10      - Surah Al-Imran, verse 10")
                print("  18:65     - Surah Al-Kahf, verse 65")
                print()
                continue
            
            # Validate input
            try:
                chapter, verse = InputValidator.validate_input(user_input)
            except ValueError as e:
                print(f" Error: {e}")
                print("Please use format 'chapter:verse' (e.g., '2:255')\n")
                continue
            
            # Ask for translation preference
            print("\n Choose translation (press Enter for default 'sahih'):")
            print("Options: sahih, pickthall, yusufali, asad, hilali, shakir, wahiduddin, clearquran")
            translation_input = input("Translation: ").strip()
            translation = translation_input if translation_input else 'sahih'
            
            if translation not in api.get_available_translations():
                print(f" Unknown translation '{translation}', using 'sahih' instead.")
                translation = 'sahih'
            
            # Ask for format preference
            print("\n Choose format (press Enter for default 'both'):")
            print("Options: arabic, translation, both")
            format_input = input("Format: ").strip()
            format_choice = format_input if format_input in ['arabic', 'translation', 'both'] else 'both'
            
            print(f"\n Fetching verse {chapter}:{verse}...")
            print("-" * 60)
            
            # Fetch verse data
            verse_data = api.get_verse(chapter, verse, translation)
            
            # Format and display output
            formatted_output = OutputFormatter.format_verse(verse_data, format_choice)
            print(formatted_output)
            
            print("-" * 60)
            print(" Would you like to fetch another verse? (y/n)")
            continue_input = input("Continue: ").strip().lower()
            
            if continue_input in ['n', 'no', 'quit', 'exit']:
                print("\n Thank you for using Quran Verse Fetcher! May Allah bless you.")
                break
            print()
            
        except KeyboardInterrupt:
            print("\n\n Thank you for using Quran Verse Fetcher! May Allah bless you.")
            break
        except Exception as e:
            print(f" An error occurred: {e}")
            print("Please try again.\n")


def main():
    """Main function to handle command-line interface"""
    parser = argparse.ArgumentParser(
        description="Fetch Quranic verses using chapter:verse format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 2:255                    # Fetch Ayat al-Kursi (Arabic only)
  %(prog)s 1:1 -t sahih            # Al-Fatiha verse 1 with Sahih International translation
  %(prog)s 3:10 -f both -o verse.txt  # Save both Arabic and translation to file
  %(prog)s 18:65 -f translation    # Show only English translation
  
Available translations:
  sahih, pickthall, yusufali, asad, hilali, shakir, wahiduddin, clearquran
        """
    )
    
    parser.add_argument(
        'verse',
        nargs='?',
        help='Verse in format "chapter:verse" (e.g., "2:255", "3:10")'
    )
    
    parser.add_argument(
        '-t', '--translation',
        choices=['sahih', 'pickthall', 'yusufali', 'asad', 'hilali', 'shakir', 'wahiduddin', 'clearquran'],
        default='sahih',
        help='Translation to include (default: sahih)'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['arabic', 'translation', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Save output to file'
    )
    
    parser.add_argument(
        '--list-translations',
        action='store_true',
        help='List available translations and exit'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Run in interactive mode to input verses'
    )
    
    args = parser.parse_args()
    
    # Handle list translations request
    if args.list_translations:
        api = QuranAPI()
        translations = api.get_available_translations()
        print("Available translations:")
        for trans in translations:
            print(f"  - {trans}")
        return
    
    # Handle interactive mode
    if args.interactive:
        run_interactive_mode()
        return
    
    # Check if verse argument is provided
    if not args.verse:
        parser.error("the following arguments are required: verse")
    
    try:
        # Validate input
        chapter, verse = InputValidator.validate_input(args.verse)
        
        # Initialize API
        api = QuranAPI()
        
        # Determine if translation is needed
        translation = args.translation if args.format in ['translation', 'both'] else None
        
        print(f"Fetching verse {chapter}:{verse}...", file=sys.stderr)
        
        # Fetch verse data
        verse_data = api.get_verse(chapter, verse, translation)
        
        # Format output
        formatted_output = OutputFormatter.format_verse(verse_data, args.format)
        
        # Display or save output
        if args.output:
            if OutputFormatter.save_to_file(formatted_output, args.output):
                print(f"Verse saved to '{args.output}'", file=sys.stderr)
            else:
                sys.exit(1)
        else:
            print(formatted_output)
    
    except ValueError as e:
        print(f"Input Error: {e}", file=sys.stderr)
        print("Use --help for usage information.", file=sys.stderr)
        sys.exit(1)
    
    except requests.RequestException as e:
        print(f"Network Error: {e}", file=sys.stderr)
        print("Please check your internet connection and try again.", file=sys.stderr)
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        print("Please try again or report this issue.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
