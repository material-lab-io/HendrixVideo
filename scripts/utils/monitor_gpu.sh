#!/bin/bash
# Monitor GPU usage continuously

echo "Monitoring GPU usage (Ctrl+C to stop)..."
echo "Time | GPU | Name | Util% | Memory Used | Process"
echo "------|-----|------|-------|-------------|--------"

while true; do
    TIME=$(date +%H:%M:%S)
    
    # Get GPU stats
    nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used --format=csv,noheader,nounits | while read line; do
        echo "$TIME | $line"
    done
    
    # Get processes using GPU
    nvidia-smi --query-compute-apps=pid,used_memory,name --format=csv,noheader,nounits 2>/dev/null | while read line; do
        if [ ! -z "$line" ]; then
            echo "      Process: $line"
        fi
    done
    
    echo "------|-----|------|-------|-------------|--------"
    sleep 2
done