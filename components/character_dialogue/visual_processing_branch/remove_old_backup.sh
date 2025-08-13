#!/bin/bash
# Script to remove old pipeline backup after verification
# Run this only after confirming the new pipeline is working in production

echo "This will permanently delete the old pipeline backup."
echo "Location: old_pipeline_backup/"
echo ""
read -p "Are you sure you want to delete the backup? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo "Removing old pipeline backup..."
    rm -rf old_pipeline_backup/
    echo "Backup removed successfully."
else
    echo "Backup removal cancelled."
fi