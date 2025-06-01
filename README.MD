# deduplicator2k

**deduplicator2k** is a command-line tool designed to help users identify and remove duplicate files within a given directory.

## Features
- Scans a specified directory for duplicate files.
- Supports a dry run to preview changes without deleting files.
- Allows restoring removed files.
- Provides verbose output for detailed logs.
- Displays a progress bar for file scanning.
- Runs in silent mode for minimal output.
- Assumes "yes" for all prompts to streamline execution.

## Installation
To use `deduplicator2k`, ensure you have Python installed. Clone or download the repository and run the script with the desired arguments.

## Usage
```bash
python deduplicator2k.py [OPTIONS]

## Example Usage
```bash
python deduplicator2k.py -d /path/to/directory -v -p

## Arguments

```
-d, --directory    # Directory to scan for duplicate files
-y, --assumeyes    # Assume "yes" to all prompts
-n, --dryrun       # Perform a dry run without deleting files
-v, --verbose      # Enable verbose output
-r, --restore      # Print removed files and allow restoration
-p, --progress     # Show a progress bar
-s, --silent       # Run in silent mode
```