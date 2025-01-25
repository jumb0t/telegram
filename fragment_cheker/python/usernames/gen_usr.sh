#!/bin/bash

# Настройки префиксов (можно добавить больше по необходимости)
PREFIXES=("tg" "ton" "btc" "eth" "nft" "crypto" "vip")

# Чтение входного файла и создание логинов
if [[ -z "$1" || -z "$2" ]]; then
    echo "Использование: $0 <входной файл> <выходной файл> [префиксы...]"
    exit 1
fi

input_file="$1"
output_file="$2"
selected_prefixes=("${PREFIXES[@]}")

# Если были переданы конкретные префиксы, используем их
if [ $# -gt 2 ]; then
    selected_prefixes=("${@:3}")
fi

# Чтение слов из файла и генерация логинов
while IFS= read -r word; do
    for prefix in "${selected_prefixes[@]}"; do
        echo "@${prefix}${word,,}"
    done
done < "$input_file" > "$output_file"

echo "Логины успешно записаны в файл: $output_file"
